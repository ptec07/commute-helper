import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def disable_live_bus_stop_search(monkeypatch):
    from app.services import search_service

    monkeypatch.setattr(search_service, '_search_live_bus_stops', lambda query: [])


def test_search_returns_matching_subway_station():
    response = client.get('/api/search/stops?q=상계역')

    assert response.status_code == 200
    payload = response.json()
    assert payload['subwayStations'][0]['name'] == '상계역'


def test_search_returns_common_station_beyond_initial_demo_fixture():
    response = client.get('/api/search/stops?q=사당역')

    assert response.status_code == 200
    payload = response.json()
    assert any(station['name'] == '사당역' for station in payload['subwayStations'])


def test_search_includes_live_seoul_and_gyeonggi_bus_stops(monkeypatch):
    from app.services import search_service

    monkeypatch.setattr(
        search_service,
        '_search_live_bus_stops',
        lambda query: [
            {
                'externalId': '122000606',
                'name': '강남역',
                'lineName': '서울버스정류장 23813',
                'kind': 'bus_stop',
                'direction': '',
            },
            {
                'externalId': '277102443',
                'name': '판교역동편',
                'lineName': '경기버스정류장',
                'kind': 'bus_stop',
                'direction': '',
            },
        ],
    )

    response = client.get('/api/search/stops?q=판교역')

    assert response.status_code == 200
    payload = response.json()
    assert any(stop['name'] == '강남역' for stop in payload['busStops'])
    assert any(stop['name'] == '판교역동편' for stop in payload['busStops'])


def test_search_includes_representative_metropolitan_stations():
    for query, expected in [
        ('종각', '종각역'),
        ('불암산', '불암산역'),
        ('판교', '판교역'),
        ('정자', '정자역'),
        ('인천시청', '인천시청역'),
        ('대화', '대화역'),
        ('의정부', '의정부역'),
    ]:
        response = client.get('/api/search/stops', params={'q': query})

        assert response.status_code == 200
        payload = response.json()
        assert any(
            station['name'] == expected for station in payload['subwayStations']
        ), f'{query} should find {expected}'


def test_search_uses_application_data_index_not_test_fixture():
    from app.services import search_service

    assert 'app/data' in search_service.SEARCH_INDEX_PATH.as_posix()
    assert 'tests/fixtures' not in search_service.SEARCH_INDEX_PATH.as_posix()


def test_search_normalizes_station_suffix_for_common_station():
    response = client.get('/api/search/stops?q=서울')

    assert response.status_code == 200
    payload = response.json()
    assert any(station['name'] == '서울역' for station in payload['subwayStations'])


def test_search_returns_empty_results_for_whitespace_only_query():
    response = client.get('/api/search/stops?q=%20%20%20')

    assert response.status_code == 200
    assert response.json() == {'busStops': [], 'subwayStations': []}


def test_search_returns_controlled_error_when_index_missing(monkeypatch):
    from app.services import search_service

    monkeypatch.setattr(
        search_service,
        'SEARCH_INDEX_PATH',
        search_service.SEARCH_INDEX_PATH.with_name('missing.json'),
    )
    response = client.get('/api/search/stops?q=상계역')

    assert response.status_code == 503
