from fastapi.testclient import TestClient

from smc_assistant.main import create_app


def test_health_returns_service_status() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "smc-assistant-api"
    assert payload["version"] == "0.1.0"
    assert "timestamp" in payload


def test_ready_returns_readiness_status() -> None:
    client = TestClient(create_app())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_cors_allows_localhost_frontend_origin() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_allows_loopback_frontend_origin() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://127.0.0.1:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
