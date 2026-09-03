from fastapi.testclient import TestClient

from smc_assistant.main import create_app


def valid_payload(
    *,
    event_id: str = "BTCUSDT-1-1767225660000-LONG",
    symbol: str = "BTCUSDT",
    htf_bias: str = "BULLISH",
) -> dict[str, object]:
    return {
        "schemaVersion": "1.0",
        "eventId": event_id,
        "eventType": "SETUP_CANDIDATE",
        "source": "TRADINGVIEW",
        "strategyVersion": "smc-rce-v1",
        "symbol": symbol,
        "exchange": "BINANCE",
        "timeframe": "1",
        "barOpenTime": "2026-01-01T12:00:00Z",
        "barCloseTime": "2026-01-01T12:01:00Z",
        "direction": "LONG",
        "marketStructure": {
            "htfTimeframe": "15",
            "htfBias": htf_bias,
            "bos": True,
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
            "takeProfit": 65580.0,
            "riskReward": 2.0,
        },
        "features": {
            "atr": None,
            "relativeVolume": None,
            "displacementScore": 0.81,
            "session": "NEW_YORK",
        },
    }


def test_lists_setup_candidates_created_from_webhooks() -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/webhooks/tradingview", json=valid_payload())
    list_response = client.get("/api/v1/setups")

    assert response.status_code == 202
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["setupId"] == "BTCUSDT-1-1767225660000-LONG"
    assert payload["items"][0]["score"] == 100.0
    assert payload["items"][0]["accepted"] is True
    assert len(payload["items"][0]["components"]) == 7


def test_gets_setup_candidate_detail_by_setup_id() -> None:
    client = TestClient(create_app())
    webhook_payload = valid_payload()
    client.post("/api/v1/webhooks/tradingview", json=webhook_payload)

    response = client.get("/api/v1/setups/BTCUSDT-1-1767225660000-LONG")

    assert response.status_code == 200
    payload = response.json()
    assert payload["setupId"] == "BTCUSDT-1-1767225660000-LONG"
    assert payload["eventId"] == "BTCUSDT-1-1767225660000-LONG"
    assert payload["symbol"] == "BTCUSDT"
    assert payload["barCloseTime"] == "2026-01-01T12:01:00+00:00"


def test_filters_setup_candidate_list_by_symbol_and_acceptance() -> None:
    client = TestClient(create_app())
    accepted_payload = valid_payload(event_id="BTCUSDT-1-1-LONG", symbol="BTCUSDT")
    rejected_payload = valid_payload(
        event_id="ETHUSDT-1-2-LONG",
        symbol="ETHUSDT",
        htf_bias="BEARISH",
    )

    client.post("/api/v1/webhooks/tradingview", json=accepted_payload)
    client.post("/api/v1/webhooks/tradingview", json=rejected_payload)

    symbol_response = client.get("/api/v1/setups", params={"symbol": "BTCUSDT"})
    rejected_response = client.get("/api/v1/setups", params={"accepted": False})

    assert symbol_response.status_code == 200
    assert [item["symbol"] for item in symbol_response.json()["items"]] == ["BTCUSDT"]
    assert rejected_response.status_code == 200
    assert [item["symbol"] for item in rejected_response.json()["items"]] == ["ETHUSDT"]
    assert rejected_response.json()["items"][0]["rejectionReasons"] == [
        "HTF_BIAS_CONFLICT"
    ]


def test_rejects_invalid_setup_list_limit() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/setups", params={"limit": 0})

    assert response.status_code == 422


def test_returns_404_for_unknown_setup_candidate() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/setups/missing-setup")

    assert response.status_code == 404
    assert response.json()["detail"] == "Setup candidate not found."
