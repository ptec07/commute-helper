from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_profile_returns_created_profile():
    response = client.post(
        '/api/commute-profiles',
        json={
            'name': '회사 가기',
            'origin_label': '집',
            'destination_label': '회사',
            'target_arrival_time': '09:00:00',
            'preferred_mode': 'balanced',
            'walking_tolerance_min': 10,
        },
    )

    assert response.status_code == 201
    assert response.json()['name'] == '회사 가기'


def test_list_profiles_returns_created_profile():
    response = client.get('/api/commute-profiles')

    assert response.status_code == 200
    assert isinstance(response.json(), list)
