from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_endpoint_returns_recommendation():
    profile = client.post(
        '/api/commute-profiles',
        json={
            'name': '회사 가기',
            'origin_label': '집',
            'destination_label': '회사',
            'target_arrival_time': '09:00:00',
            'preferred_mode': 'balanced',
            'walking_tolerance_min': 10,
        },
    ).json()

    client.post(
        f"/api/commute-profiles/{profile['id']}/stops",
        json={
            'type': 'subway_station',
            'external_id': 'station-100',
            'name': '상계역',
            'line_name': '4호선',
            'direction': '오이도방향',
            'sort_order': 1,
        },
    )

    response = client.get(f"/api/dashboard/{profile['id']}")
    assert response.status_code == 200
    assert 'recommendation' in response.json()


def test_dashboard_endpoint_returns_controlled_error_when_fixture_missing(monkeypatch):
    from app.services import dashboard_service

    profile = client.post(
        '/api/commute-profiles',
        json={
            'name': '회사 가기',
            'origin_label': '집',
            'destination_label': '회사',
            'target_arrival_time': '09:00:00',
            'preferred_mode': 'balanced',
            'walking_tolerance_min': 10,
        },
    ).json()

    monkeypatch.setattr(dashboard_service, 'FIXTURES', dashboard_service.FIXTURES.with_name('missing-dir'))
    response = client.get(f"/api/dashboard/{profile['id']}")
    assert response.status_code == 503
