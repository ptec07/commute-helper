from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint_returns_ok():
    client = TestClient(app)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_cors_preflight_allows_local_vite_frontend():
    client = TestClient(app)
    response = client.options(
        '/api/commute-profiles',
        headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
        },
    )

    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'
