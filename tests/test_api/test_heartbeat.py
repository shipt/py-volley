from starlette.testclient import TestClient

from app.main import get_app

app = get_app()


def test_heartbeat(test_client: TestClient) -> None:
    response = test_client.get("/api/health/heartbeat")
    assert response.status_code == 200
    assert response.json() == {"is_alive": True}


def test_default_route(test_client: TestClient) -> None:
    response = test_client.get("/")
    assert response.status_code == 404
