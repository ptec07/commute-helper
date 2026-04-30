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
