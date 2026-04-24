from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_add_stop_to_profile():
    create = client.post(
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

    response = client.post(
        f"/api/commute-profiles/{create['id']}/stops",
        json={
            'type': 'subway_station',
            'external_id': 'station-100',
            'name': '상계역',
            'line_name': '4호선',
            'direction': '오이도방향',
            'sort_order': 1,
        },
    )

    assert response.status_code == 201
    assert response.json()['name'] == '상계역'

    profiles = client.get('/api/commute-profiles').json()
    matching = [item for item in profiles if item['id'] == create['id']][0]
    assert len(matching['stops']) == 1


def test_rejects_unsupported_stop_type_with_validation_error():
    create = client.post(
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

    response = client.post(
        f"/api/commute-profiles/{create['id']}/stops",
        json={
            'type': 'tram_stop',
            'external_id': 'bad-stop',
            'name': '잘못된 정류장',
            'sort_order': 1,
        },
    )

    assert response.status_code == 422
