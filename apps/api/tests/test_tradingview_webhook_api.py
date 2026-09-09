from copy import deepcopy
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from smc_assistant.application.audit import AuditEvent, AuditEventType
from smc_assistant.config import Settings
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
    assert payload["setupCandidateId"] == "BTCUSDT-1m-1720000000-bullish-choch"
    assert payload["setupScore"]["score"] == 100.0
    assert payload["setupScore"]["accepted"] is True
    assert payload["setupScore"]["configVersion"] == "rule-score-v1"
    assert payload["setupScore"]["rejectionReasons"] == []
    assert len(payload["setupScore"]["components"]) == 7
    assert payload["message"] == "TradingView webhook payload accepted for processing."
    assert payload["paperTradeAutomation"]["status"] == "CREATED"
    assert payload["paperTradeAutomation"]["tradeStatus"] == "PENDING"
    assert payload["paperTradeAutomation"]["tradeId"] is not None


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
    assert payload["setupCandidateId"] == first_response.json()["setupCandidateId"]
    assert payload["setupScore"] == first_response.json()["setupScore"]
    assert payload["message"] == "TradingView webhook payload was already accepted."
    assert payload["paperTradeAutomation"]["status"] == "EXISTING"
    assert payload["paperTradeAutomation"]["tradeId"] == first_response.json()[
        "paperTradeAutomation"
    ]["tradeId"]


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


def test_market_price_webhooks_open_and_close_automatic_paper_trade_idempotently() -> None:
    client = TestClient(create_app())
    setup_response = client.post("/api/v1/webhooks/tradingview", json=valid_payload())
    setup_result = setup_response.json()
    trade_id = setup_result["paperTradeAutomation"]["tradeId"]
    first_received_at = datetime.fromisoformat(setup_result["receivedAt"])

    open_event = {
        "schemaVersion": "1.0",
        "eventId": "BTCUSDT-1-live-open-PRICE",
        "eventType": "MARKET_PRICE",
        "source": "TRADINGVIEW",
        "symbol": "BTCUSDT",
        "exchange": "BINANCE",
        "timeframe": "1",
        "observedAt": (first_received_at + timedelta(seconds=1)).isoformat(),
        "price": 65180,
    }
    opened = client.post("/api/v1/webhooks/tradingview", json=open_event)

    assert opened.status_code == 202, opened.text
    assert opened.json()["status"] == "ACCEPTED"
    assert opened.json()["matchedTrades"] == 1
    assert opened.json()["updatedTrades"] == [
        {"tradeId": trade_id, "status": "OPEN", "revision": 2}
    ]

    duplicate = client.post("/api/v1/webhooks/tradingview", json=open_event)
    assert duplicate.status_code == 202
    assert duplicate.json()["status"] == "DUPLICATE"
    assert duplicate.json()["matchedTrades"] == 0
    assert client.get(f"/api/v1/paper-trades/{trade_id}").json()["revision"] == 2

    close_event = {
        **open_event,
        "eventId": "BTCUSDT-1-live-close-PRICE",
        "observedAt": (first_received_at + timedelta(seconds=2)).isoformat(),
        "price": 65800,
    }
    closed = client.post("/api/v1/webhooks/tradingview", json=close_event)

    assert closed.status_code == 202
    assert closed.json()["updatedTrades"][0]["status"] == "CLOSED"
    trade = client.get(f"/api/v1/paper-trades/{trade_id}").json()
    assert trade["exitReason"] == "TAKE_PROFIT"
    assert trade["realizedR"] == 3
    events = client.get(f"/api/v1/paper-trades/{trade_id}/events").json()["items"]
    assert [event["eventType"] for event in events] == ["CREATED", "OPENED", "CLOSED"]


def test_market_price_webhook_rejects_event_id_owned_by_setup() -> None:
    client = TestClient(create_app())
    setup = valid_payload()
    assert client.post("/api/v1/webhooks/tradingview", json=setup).status_code == 202
    collision = {
        "schemaVersion": "1.0",
        "eventId": setup["eventId"],
        "eventType": "MARKET_PRICE",
        "source": "TRADINGVIEW",
        "symbol": "BTCUSDT",
        "exchange": "BINANCE",
        "timeframe": "1",
        "observedAt": "2026-09-09T12:00:00Z",
        "price": 65180,
    }

    response = client.post("/api/v1/webhooks/tradingview", json=collision)

    assert response.status_code == 409


def test_setup_webhook_reports_disabled_and_risk_rejected_automation() -> None:
    disabled_client = TestClient(
        create_app(Settings(paper_auto_trade_enabled=False))
    )
    disabled = disabled_client.post(
        "/api/v1/webhooks/tradingview", json=valid_payload()
    )

    assert disabled.status_code == 202
    assert disabled.json()["paperTradeAutomation"]["status"] == "DISABLED"
    assert disabled_client.get("/api/v1/paper-trades").json()["count"] == 0

    risk_client = TestClient(
        create_app(
            Settings(
                paper_default_risk_percent=2,
                paper_max_risk_per_trade_percent=1,
            )
        )
    )
    rejected = risk_client.post(
        "/api/v1/webhooks/tradingview", json=valid_payload()
    )

    assert rejected.status_code == 202
    assert rejected.json()["status"] == "ACCEPTED"
    assert rejected.json()["paperTradeAutomation"]["status"] == "RISK_REJECTED"
    assert "RISK_PER_TRADE_EXCEEDED" in rejected.json()["paperTradeAutomation"][
        "message"
    ]
    assert risk_client.get("/api/v1/paper-trades").json()["count"] == 0
