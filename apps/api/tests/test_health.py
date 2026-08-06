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

