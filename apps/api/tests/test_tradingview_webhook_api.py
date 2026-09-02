from copy import deepcopy

from fastapi.testclient import TestClient

from smc_assistant.application.audit import AuditEvent, AuditEventType
from smc_assistant.main import create_app


class RecordingAuditLogger:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


def valid_payload() -> dict[str, object]:
    return {
        "schemaVersion": "1.0",
        "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
        "eventType": "SETUP_CANDIDATE",
        "source": "TRADINGVIEW",
        "strategyVersion": "smc-rce-v1",
        "symbol": "BTCUSDT",
        "exchange": "BINANCE",
        "timeframe": "1",
        "barOpenTime": "2026-01-01T12:00:00Z",
        "barCloseTime": "2026-01-01T12:01:00Z",
        "direction": "LONG",
        "marketStructure": {
            "htfTimeframe": "15",
            "htfBias": "BULLISH",
            "bos": False,
            "choch": True,
            "liquiditySweep": True,
        },
        "fvg": {
            "lower": 65120.0,
            "upper": 65240.0,
            "equilibrium": 65180.0,
            "sizeAtrRatio": 0.42,
            "mitigationPercent": 0.0,
        },
        "execution": {
            "entry": 65180.0,
            "stopLoss": 64980.0,
            "takeProfit": 65780.0,
            "riskReward": 3.0,
        },
        "features": {
            "atr": 285.0,
            "relativeVolume": 1.7,
            "displacementScore": 0.81,
            "session": "NEW_YORK",
        },
    }


def test_tradingview_webhook_accepts_valid_payload() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/webhooks/tradingview", json=valid_payload())

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "ACCEPTED"
    assert payload["eventId"] == "BTCUSDT-1m-1720000000-bullish-choch"
    assert payload["eventType"] == "SETUP_CANDIDATE"
    assert payload["schemaVersion"] == "1.0"
    assert "receivedAt" in payload
    assert payload["firstReceivedAt"] == payload["receivedAt"]
    assert payload["message"] == "TradingView webhook payload accepted for processing."


def test_tradingview_webhook_marks_repeated_event_id_as_duplicate() -> None:
    client = TestClient(create_app())

    first_response = client.post("/api/v1/webhooks/tradingview", json=valid_payload())
    second_response = client.post("/api/v1/webhooks/tradingview", json=valid_payload())

    assert first_response.status_code == 202
    assert second_response.status_code == 202
    payload = second_response.json()
    assert payload["status"] == "DUPLICATE"
    assert payload["eventId"] == "BTCUSDT-1m-1720000000-bullish-choch"
    assert payload["firstReceivedAt"] == first_response.json()["receivedAt"]
    assert payload["message"] == "TradingView webhook payload was already accepted."


def test_tradingview_webhook_rejects_invalid_payload() -> None:
    client = TestClient(create_app())
    raw_payload = valid_payload()
    execution = deepcopy(raw_payload["execution"])
    assert isinstance(execution, dict)
    execution["riskReward"] = 2.0
    raw_payload["execution"] = execution

    response = client.post("/api/v1/webhooks/tradingview", json=raw_payload)

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error"


def test_tradingview_webhook_validation_response_does_not_echo_raw_secret() -> None:
    app = create_app()
    audit_logger = RecordingAuditLogger()
    app.state.audit_logger = audit_logger
    client = TestClient(app)
    raw_payload = valid_payload()
    raw_payload["secret"] = "super-secret-value"

    response = client.post("/api/v1/webhooks/tradingview", json=raw_payload)

    assert response.status_code == 422
    assert "super-secret-value" not in response.text
    assert audit_logger.events[0].event_type == AuditEventType.WEBHOOK_VALIDATION_FAILED
    assert audit_logger.events[0].metadata["path"] == "/api/v1/webhooks/tradingview"
    assert "super-secret-value" not in str(audit_logger.events[0].metadata)
