from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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

    monkeypatch.setattr(search_service, 'FIXTURE_PATH', search_service.FIXTURE_PATH.with_name('missing.json'))
    response = client.get('/api/search/stops?q=상계역')

    assert response.status_code == 503
