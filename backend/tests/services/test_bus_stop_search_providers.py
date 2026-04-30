import httpx
import pytest

from app.services.providers.bus_stop_search import (
    GyeonggiBusStopSearchProvider,
    SeoulBusStopSearchProvider,
)


class FakeResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError('bad status', request=None, response=None)


def test_seoul_bus_stop_search_fetches_and_normalizes_xml(monkeypatch):
    calls = []
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <ServiceResult><msgHeader><headerCd>0</headerCd></msgHeader><msgBody>
      <itemList><stId>122000606</stId><stNm>강남역</stNm><arsId>23813</arsId></itemList>
    </msgBody></ServiceResult>'''

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        return FakeResponse(xml)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusStopSearchProvider(service_key='secret', request_timeout=1.5)
    result = provider.fetch('강남역')

    assert result == [
        {
            'externalId': '122000606',
            'name': '강남역',
            'lineName': '서울버스정류장 23813',
            'kind': 'bus_stop',
            'direction': '',
        }
    ]
    assert calls[0][0] == 'http://ws.bus.go.kr/api/rest/stationinfo/getStationByName'
    assert calls[0][1]['stSrch'] == '강남역'
    assert calls[0][2] == 1.5


def test_gyeonggi_bus_stop_search_fetches_and_normalizes_xml(monkeypatch):
    calls = []
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <response><msgHeader><resultCode>0</resultCode></msgHeader><msgBody>
      <busStationList><stationId>277102443</stationId><stationName>판교역동편</stationName></busStationList>
    </msgBody></response>'''

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        return FakeResponse(xml)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = GyeonggiBusStopSearchProvider(service_key='secret')
    result = provider.fetch('판교역')

    assert result == [
        {
            'externalId': '277102443',
            'name': '판교역동편',
            'lineName': '경기버스정류장',
            'kind': 'bus_stop',
            'direction': '',
        }
    ]
    assert calls[0][0] == 'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2'
    assert calls[0][1]['keyword'] == '판교역'


def test_gyeonggi_bus_stop_search_falls_back_to_bus_realtime_route_station_api(monkeypatch):
    calls = []
    route_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <response><msgHeader><resultCode>0</resultCode></msgHeader><msgBody>
      <busRouteList><routeId>222000107</routeId><routeName>1001</routeName></busRouteList>
    </msgBody></response>'''
    stations_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <response><msgHeader><resultCode>0</resultCode></msgHeader><msgBody>
      <busRouteStationList><stationId>222001626</stationId><stationName>청학리</stationName><mobileNo>49337</mobileNo></busRouteStationList>
      <busRouteStationList><stationId>222001300</stationId><stationName>극동마이다스빌.다우에코빌</stationName><mobileNo>23811</mobileNo></busRouteStationList>
    </msgBody></response>'''

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        if url == 'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2':
            return FakeResponse('Forbidden', status_code=403)
        if url == 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteListv2':
            return FakeResponse(route_xml)
        if url == 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2':
            return FakeResponse(stations_xml)
        raise AssertionError(f'unexpected url: {url}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = GyeonggiBusStopSearchProvider(service_key='secret')
    result = provider.fetch('1001')

    assert result == [
        {
            'externalId': '222001626',
            'name': '청학리',
            'lineName': '경기버스정류장 49337',
            'kind': 'bus_stop',
            'direction': '1001번 노선',
        },
        {
            'externalId': '222001300',
            'name': '극동마이다스빌.다우에코빌',
            'lineName': '경기버스정류장 23811',
            'kind': 'bus_stop',
            'direction': '1001번 노선',
        },
    ]
    assert calls[0][0] == 'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2'
    assert calls[1][0] == 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteListv2'
    assert calls[1][1] == {'serviceKey': 'secret', 'keyword': '1001', 'format': 'xml'}
    assert calls[2][0] == 'https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteStationListv2'
    assert calls[2][1] == {'serviceKey': 'secret', 'routeId': '222000107', 'format': 'xml'}


def test_gyeonggi_bus_stop_search_skips_route_fallback_for_station_name_queries(monkeypatch):
    calls = []

    def fake_get(url, params, timeout):
        calls.append((url, params, timeout))
        if url == 'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2':
            return FakeResponse('Forbidden', status_code=403)
        raise AssertionError(f'unexpected route fallback url for station query: {url}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = GyeonggiBusStopSearchProvider(service_key='secret')

    with pytest.raises(OSError):
        provider.fetch('판교역')

    assert [call[0] for call in calls] == [
        'https://apis.data.go.kr/6410000/busstationservice/v2/getBusStationListv2'
    ]


def test_bus_stop_search_provider_raises_oserror_for_auth_failure(monkeypatch):
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <ServiceResult><msgHeader><headerCd>7</headerCd><headerMsg>Key인증실패</headerMsg></msgHeader></ServiceResult>'''

    monkeypatch.setattr(httpx, 'get', lambda *args, **kwargs: FakeResponse(xml))

    provider = SeoulBusStopSearchProvider(service_key='bad')

    with pytest.raises(OSError):
        provider.fetch('강남역')
