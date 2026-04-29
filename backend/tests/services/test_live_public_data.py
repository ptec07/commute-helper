from datetime import datetime, time
from pathlib import Path

import httpx
import pytest

from app.models.commute_profile import CommuteProfile
from app.models.commute_stop import CommuteStop
from app.schemas.provider_models import BusArrival, SubwayArrival
from app.services.dashboard_service import build_dashboard
from app.services.providers.odsay_bus_arrival import ODsayBusArrivalProvider
from app.services.providers.odsay_bus_position import ODsayBusPositionProvider
from app.services.providers.odsay_subway_arrival import ODsaySubwayArrivalProvider
from app.services.providers.seoul_bus_arrival import SeoulBusArrivalProvider
from app.services.providers.seoul_bus_position import SeoulBusPositionProvider
from app.services.providers.seoul_subway_arrival import SeoulSubwayArrivalProvider


class DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_bus_arrival_provider_fetches_live_xml(monkeypatch):
    xml_text = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8')
    captured = {}

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        captured['url'] = url
        captured['params'] = params
        captured['timeout'] = timeout
        return DummyResponse(xml_text)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='live-key')
    arrivals = provider.fetch(stop_id='200000123')

    assert captured['url'] == 'https://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId'
    assert captured['params']['serviceKey'] == 'live-key'
    assert captured['params']['stId'] == '200000123'
    assert arrivals[0].route_name == '146'


def test_bus_arrival_provider_retries_with_http_when_insecure_fallback_enabled(monkeypatch):
    xml_text = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8')
    calls = []

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        calls.append(url)
        if url.startswith('https://'):
            raise httpx.ConnectTimeout('timed out')
        return DummyResponse(xml_text)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='live-key', allow_insecure_http_fallback=True)
    arrivals = provider.fetch(stop_id='200000123')

    assert calls == [
        'https://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId',
        'http://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId',
    ]
    assert arrivals[0].route_name == '146'


def test_bus_arrival_provider_raises_controlled_error_for_non_xml_payload(monkeypatch):
    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse('{"error":"invalid key"}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='bad-key')
    with pytest.raises(OSError):
        provider.fetch(stop_id='200000123')


def test_bus_arrival_provider_raises_controlled_error_for_invalid_numeric_xml(monkeypatch):
    payload = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8').replace('240', '곧도착', 1)

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='bad-key')
    with pytest.raises(OSError):
        provider.fetch(stop_id='200000123')


def test_bus_arrival_provider_raises_controlled_error_for_auth_failure_xml(monkeypatch):
    payload = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ServiceResult>
  <msgHeader>
    <headerCd>7</headerCd>
    <headerMsg>Key인증실패: SERVICE KEY IS NOT REGISTERED ERROR.[인증모듈 에러코드(30)]</headerMsg>
    <itemCount>0</itemCount>
  </msgHeader>
  <msgBody/>
</ServiceResult>'''

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='bad-key')
    with pytest.raises(OSError, match='SERVICE KEY IS NOT REGISTERED'):
        provider.fetch(stop_id='200000123')


def test_bus_arrival_provider_returns_empty_list_for_no_results_xml(monkeypatch):
    payload = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ServiceResult>
  <msgHeader>
    <headerCd>4</headerCd>
    <headerMsg>결과가 없습니다.</headerMsg>
    <itemCount>0</itemCount>
  </msgHeader>
  <msgBody/>
</ServiceResult>'''

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusArrivalProvider(service_key='live-key')
    assert provider.fetch(stop_id='100000001') == []


def test_bus_position_provider_fetches_live_json(monkeypatch):
    payload = Path('tests/fixtures/seoul_bus_position.json').read_text(encoding='utf-8')
    captured = {}

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        captured['url'] = url
        captured['params'] = params
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='live-key')
    positions = provider.fetch(route_id='100000146')

    assert captured['url'] == 'https://ws.bus.go.kr/api/rest/buspos/getLowBusPosByRtid'
    assert captured['params']['busRouteId'] == '100000146'
    assert positions[0].route_id == '100000146'


def test_bus_position_provider_retries_with_http_when_insecure_fallback_enabled(monkeypatch):
    payload = Path('tests/fixtures/seoul_bus_position.xml').read_text(encoding='utf-8')
    calls = []

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        calls.append(url)
        if url.startswith('https://'):
            raise httpx.ConnectTimeout('timed out')
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='live-key', allow_insecure_http_fallback=True)
    positions = provider.fetch(route_id='100000146')

    assert calls == [
        'https://ws.bus.go.kr/api/rest/buspos/getLowBusPosByRtid',
        'http://ws.bus.go.kr/api/rest/buspos/getLowBusPosByRtid',
    ]
    assert positions[0].route_id == '100000146'


def test_bus_position_provider_fetches_live_xml(monkeypatch):
    payload = Path('tests/fixtures/seoul_bus_position.xml').read_text(encoding='utf-8')

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='live-key')
    positions = provider.fetch(route_id='100000146')

    assert positions[0].route_id == '100000146'
    assert positions[0].station_count_from_target == 2


def test_bus_position_provider_raises_controlled_error_for_malformed_payload(monkeypatch):
    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse('not-a-valid-payload')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='bad-key')
    with pytest.raises(OSError):
        provider.fetch(route_id='100000146')


def test_bus_position_provider_raises_controlled_error_for_auth_failure_xml(monkeypatch):
    payload = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ServiceResult>
  <msgHeader>
    <headerCd>7</headerCd>
    <headerMsg>Key인증실패: SERVICE KEY IS NOT REGISTERED ERROR.[인증모듈 에러코드(30)]</headerMsg>
    <itemCount>0</itemCount>
  </msgHeader>
  <msgBody/>
</ServiceResult>'''

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='bad-key')
    with pytest.raises(OSError, match='SERVICE KEY IS NOT REGISTERED'):
        provider.fetch(route_id='100000146')


def test_bus_position_provider_returns_empty_list_for_no_results_xml(monkeypatch):
    payload = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ServiceResult>
  <msgHeader>
    <headerCd>4</headerCd>
    <headerMsg>결과가 없습니다.</headerMsg>
    <itemCount>0</itemCount>
  </msgHeader>
  <msgBody/>
</ServiceResult>'''

    def fake_get(url: str, *, params: dict[str, str], timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulBusPositionProvider(service_key='live-key')
    assert provider.fetch(route_id='204000190') == []


def test_subway_arrival_provider_fetches_live_xml(monkeypatch):
    xml_text = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8')
    captured = {}

    def fake_get(url: str, *, timeout: float):
        captured['url'] = url
        return DummyResponse(xml_text)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulSubwayArrivalProvider(service_key='seoul-live-key')
    arrivals = provider.fetch(station_name='상계역')

    assert captured['url'].startswith(
        'https://swopenAPI.seoul.go.kr/api/subway/seoul-live-key/xml/realtimeStationArrival/0/5/'
    )
    assert '%EC%83%81%EA%B3%84' in captured['url']
    assert '%EC%97%AD' not in captured['url']
    assert arrivals[0].station_name == '상계역'


def test_subway_arrival_provider_retries_with_http_when_insecure_fallback_enabled(monkeypatch):
    xml_text = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8')
    calls = []

    def fake_get(url: str, *, timeout: float):
        calls.append(url)
        if url.startswith('https://'):
            raise httpx.ConnectTimeout('timed out')
        return DummyResponse(xml_text)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulSubwayArrivalProvider(service_key='seoul-live-key', allow_insecure_http_fallback=True)
    arrivals = provider.fetch(station_name='상계역')

    assert calls == [
        'https://swopenAPI.seoul.go.kr/api/subway/seoul-live-key/xml/realtimeStationArrival/0/5/%EC%83%81%EA%B3%84',
        'http://swopenAPI.seoul.go.kr/api/subway/seoul-live-key/xml/realtimeStationArrival/0/5/%EC%83%81%EA%B3%84',
    ]
    assert arrivals[0].station_name == '상계역'


def test_subway_arrival_provider_raises_controlled_error_for_non_xml_payload(monkeypatch):
    def fake_get(url: str, *, timeout: float):
        return DummyResponse('{"errorMessage":{"status":500,"code":"INFO-200","message":"invalid key"}}')

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulSubwayArrivalProvider(service_key='invalid-key')
    with pytest.raises(OSError):
        provider.fetch(station_name='상계역')


def test_subway_arrival_provider_raises_controlled_error_for_invalid_numeric_xml(monkeypatch):
    payload = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8').replace('420', '곧도착', 1)

    def fake_get(url: str, *, timeout: float):
        return DummyResponse(payload)

    monkeypatch.setattr(httpx, 'get', fake_get)

    provider = SeoulSubwayArrivalProvider(service_key='invalid-key')
    with pytest.raises(OSError):
        provider.fetch(station_name='상계역')


def test_dashboard_falls_back_to_fixture_data_when_live_fetch_fails(monkeypatch):
    profile = CommuteProfile(
        id='profile-live-fallback',
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
        preferred_mode='balanced',
        walking_tolerance_min=10,
        created_at=datetime(2026, 4, 24, 9, 0, 0),
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    profile.stops = [
        CommuteStop(
            id='stop-subway-fallback',
            type='subway_station',
            external_id='1004000409',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=1,
        )
    ]

    monkeypatch.setattr(
        'app.services.dashboard_service.get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'use_live_public_data': True,
                'public_data_service_key': 'bus-live-key',
                'seoul_open_api_key': 'subway-live-key',
            },
        )(),
    )
    monkeypatch.setattr(SeoulSubwayArrivalProvider, 'fetch', lambda self, station_name: (_ for _ in ()).throw(OSError('boom')))

    dashboard = build_dashboard(profile)

    assert dashboard.subway
    assert dashboard.subway[0].station_name == '상계역'


def test_dashboard_uses_public_data_before_odsay_backup(monkeypatch):
    profile = CommuteProfile(
        id='profile-live-1',
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
        preferred_mode='balanced',
        walking_tolerance_min=10,
        created_at=datetime(2026, 4, 24, 9, 0, 0),
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    profile.stops = [
        CommuteStop(
            id='stop-bus-1',
            type='bus_stop',
            external_id='200000123',
            name='상계주공7단지',
            sort_order=1,
        ),
        CommuteStop(
            id='stop-subway-1',
            type='subway_station',
            external_id='1004000409',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=2,
        ),
    ]

    monkeypatch.setattr(
        'app.services.dashboard_service.get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'use_live_public_data': True,
                'public_data_service_key': 'bus-live-key',
                'seoul_open_api_key': 'subway-live-key',
                'allow_insecure_seoul_transit_http': False,
                'odsay_api_key': 'odsay-live-key',
            },
        )(),
    )

    bus_xml = Path('tests/fixtures/seoul_bus_arrival.xml').read_text(encoding='utf-8')
    bus_json = Path('tests/fixtures/seoul_bus_position.json').read_text(encoding='utf-8')
    subway_xml = Path('tests/fixtures/seoul_subway_arrival.xml').read_text(encoding='utf-8')

    monkeypatch.setattr(SeoulBusArrivalProvider, 'fetch', lambda self, stop_id: self.parse(bus_xml))
    monkeypatch.setattr(SeoulBusPositionProvider, 'fetch', lambda self, route_id: self.parse(bus_json))
    monkeypatch.setattr(SeoulSubwayArrivalProvider, 'fetch', lambda self, station_name: self.parse(subway_xml))
    monkeypatch.setattr(
        ODsayBusArrivalProvider,
        'fetch',
        lambda self, stop_name, stop_local_id=None: (_ for _ in ()).throw(AssertionError('ODsay backup should not run')),
    )

    dashboard = build_dashboard(profile)

    assert dashboard.bus
    assert dashboard.bus_positions
    assert dashboard.subway
    assert dashboard.profile.stops[0].external_id == '200000123'


def test_dashboard_matches_subway_station_name_with_trailing_station_suffix(monkeypatch):
    profile = CommuteProfile(
        id='profile-subway-alias-1',
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
        preferred_mode='balanced',
        walking_tolerance_min=10,
        created_at=datetime(2026, 4, 24, 9, 0, 0),
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    profile.stops = [
        CommuteStop(
            id='stop-subway-alias-1',
            type='subway_station',
            external_id='1004000410',
            name='상계역',
            line_name='4호선',
            direction='진접방향',
            sort_order=1,
        )
    ]

    monkeypatch.setattr(
        'app.services.dashboard_service.get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'use_live_public_data': True,
                'public_data_service_key': 'bus-live-key',
                'seoul_open_api_key': 'subway-live-key',
                'allow_insecure_seoul_transit_http': False,
            },
        )(),
    )
    monkeypatch.setattr(SeoulSubwayArrivalProvider, 'fetch', lambda self, station_name: [
        SubwayArrival(
            station_id='1004000410',
            station_name='상계',
            line_name='4호선',
            direction='진접방향',
            arrival_in_sec=120,
            train_type='일반',
        )
    ])

    dashboard = build_dashboard(profile)

    assert dashboard.subway
    assert dashboard.subway[0].station_name == '상계'


def test_dashboard_falls_back_to_odsay_when_public_data_live_fetch_fails(monkeypatch):
    profile = CommuteProfile(
        id='profile-live-backup-1',
        name='회사 가기',
        origin_label='집',
        destination_label='회사',
        target_arrival_time=time(hour=9),
        preferred_mode='balanced',
        walking_tolerance_min=10,
        created_at=datetime(2026, 4, 24, 9, 0, 0),
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    profile.stops = [
        CommuteStop(
            id='stop-bus-backup-1',
            type='bus_stop',
            external_id='200000123',
            name='상계주공7단지',
            sort_order=1,
        ),
        CommuteStop(
            id='stop-subway-backup-1',
            type='subway_station',
            external_id='1004000409',
            name='상계역',
            line_name='4호선',
            direction='오이도방향',
            sort_order=2,
        ),
    ]

    monkeypatch.setattr(
        'app.services.dashboard_service.get_settings',
        lambda: type(
            'Settings',
            (),
            {
                'use_live_public_data': True,
                'public_data_service_key': 'bus-live-key',
                'seoul_open_api_key': 'subway-live-key',
                'allow_insecure_seoul_transit_http': False,
                'odsay_api_key': 'odsay-live-key',
            },
        )(),
    )

    monkeypatch.setattr(
        SeoulBusArrivalProvider,
        'fetch',
        lambda self, stop_id: (_ for _ in ()).throw(OSError('public data down')),
    )
    monkeypatch.setattr(
        ODsayBusArrivalProvider,
        'fetch',
        lambda self, stop_name, stop_local_id=None: [
            BusArrival(
                route_id='100100118',
                route_name='146',
                stop_id=stop_local_id or '200000123',
                stop_name=stop_name,
                arrival_in_sec=300,
                arrival_message='약 5분 간격 운행',
                is_last_bus=False,
            )
        ],
    )
    monkeypatch.setattr(ODsayBusPositionProvider, 'fetch', lambda self, route_id: [])
    monkeypatch.setattr(
        ODsaySubwayArrivalProvider,
        'fetch',
        lambda self, station_name, line_name=None: [
            SubwayArrival(
                station_id='130',
                station_name=station_name,
                line_name=line_name or '4호선',
                direction='오이도',
                arrival_in_sec=420,
                train_type='general',
            )
        ],
    )

    dashboard = build_dashboard(profile)

    assert dashboard.bus
    assert dashboard.bus[0].arrival_message == '약 5분 간격 운행'
    assert dashboard.bus_positions == []
    assert dashboard.subway
