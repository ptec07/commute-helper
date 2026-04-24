from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_search_returns_matching_subway_station():
    response = client.get('/api/search/stops?q=상계역')

    assert response.status_code == 200
    payload = response.json()
    assert payload['subwayStations'][0]['name'] == '상계역'


def test_search_returns_empty_results_for_whitespace_only_query():
    response = client.get('/api/search/stops?q=%20%20%20')

    assert response.status_code == 200
    assert response.json() == {'busStops': [], 'subwayStations': []}


def test_search_returns_controlled_error_when_index_missing(monkeypatch):
    from app.services import search_service

    monkeypatch.setattr(search_service, 'FIXTURE_PATH', search_service.FIXTURE_PATH.with_name('missing.json'))
    response = client.get('/api/search/stops?q=상계역')

    assert response.status_code == 503
