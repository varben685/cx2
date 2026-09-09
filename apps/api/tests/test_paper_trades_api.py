from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from uuid import uuid4

from fastapi.testclient import TestClient
from test_setups_api import valid_payload

from smc_assistant.config import Settings
from smc_assistant.main import create_app


def create_setup(client: TestClient, **changes: object) -> dict[str, object]:
    payload = valid_payload()
    payload.update(changes)
    response = client.post("/api/v1/webhooks/tradingview", json=payload)
    assert response.status_code == 202, response.text
    return payload


def create_trade(client: TestClient, setup_id: str) -> dict[str, object]:
    response = client.post(
        "/api/v1/paper-trades",
        json={"setupId": setup_id, "accountBalance": 10_000, "riskPercent": 1},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_creates_opens_and_closes_paper_trade_at_target() -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    setup = create_setup(client)
    trade = create_trade(client, str(setup["eventId"]))

    assert trade["status"] == "PENDING"
    assert trade["riskAmount"] == 100
    assert trade["quantity"] == 0.5
    assert trade["riskDecision"]["approved"] is True
    assert trade["outcomeId"] is None
    assert trade["outcomeLabel"] is None
    trade_id = trade["tradeId"]

    pending = client.post(f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 65190})
    assert pending.status_code == 200
    assert pending.json()["status"] == "PENDING"

    opened = client.post(f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 65180})
    assert opened.status_code == 200
    assert opened.json()["status"] == "OPEN"

    closed = client.post(f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 65590})
    assert closed.status_code == 200
    result = closed.json()
    assert result["status"] == "CLOSED"
    assert result["exitReason"] == "TAKE_PROFIT"
    assert result["exitPrice"] == 65580
    assert result["realizedPnl"] == 200
    assert result["realizedR"] == 2
    assert result["outcomeId"] is not None
    assert result["outcomeLabel"] == "WIN"

    outcomes = client.get("/api/v1/outcomes/paper-trades").json()
    assert outcomes["count"] == 1
    outcome = outcomes["items"][0]
    assert outcome["outcomeId"] == result["outcomeId"]
    assert outcome["runId"] == "00000000-0000-0000-0000-000000000007"
    assert outcome["engineVersion"] == "paper-execution-v1"
    assert len(outcome["marketDataSha256"]) == 64
    assert outcome["outcome"]["label"] == "WIN"
    assert outcome["outcome"]["exitReason"] == "TAKE_PROFIT_HIT"
    assert outcome["outcome"]["netRealizedR"] == 2
    assert outcome["outcome"]["costs"]["totalAmount"] == 0

    events = client.get(f"/api/v1/paper-trades/{trade_id}/events").json()
    assert events["count"] == 4
    assert [item["eventType"] for item in events["items"]] == [
        "CREATED",
        "PRICE_OBSERVED",
        "OPENED",
        "CLOSED",
    ]
    assert [item["sequence"] for item in events["items"]] == [1, 2, 3, 4]

    reconciliation = client.post("/api/v1/outcomes/paper-trades/reconcile").json()
    assert reconciliation == {
        "runId": "00000000-0000-0000-0000-000000000007",
        "scanned": 1,
        "created": 0,
        "existing": 1,
    }


def test_supports_manual_close_cancel_filters_and_conflicts() -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    first = create_setup(client)
    first_trade = create_trade(client, str(first["eventId"]))
    trade_id = first_trade["tradeId"]
    assert client.post(
        f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 65180}
    ).status_code == 200
    manually_closed = client.post(
        f"/api/v1/paper-trades/{trade_id}/close", json={"exitPrice": 65380}
    )
    assert manually_closed.status_code == 200
    assert manually_closed.json()["exitReason"] == "MANUAL"
    assert manually_closed.json()["realizedR"] == 1
    assert manually_closed.json()["outcomeLabel"] == "WIN"
    assert client.post(
        f"/api/v1/paper-trades/{trade_id}/close", json={"exitPrice": 65380}
    ).status_code == 409

    second_payload = deepcopy(valid_payload())
    second_payload["eventId"] = "ETHUSDT-1-paper-cancel"
    second_payload["symbol"] = "ETHUSDT"
    second = create_setup(client, **second_payload)
    second_trade = create_trade(client, str(second["eventId"]))
    cancelled = client.post(
        f"/api/v1/paper-trades/{second_trade['tradeId']}/cancel", json={}
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    assert cancelled.json()["exitReason"] == "CANCELLED"
    assert cancelled.json()["outcomeLabel"] == "CANCELLED"

    closed_list = client.get("/api/v1/paper-trades", params={"status": "CLOSED"}).json()
    assert closed_list["count"] == 1
    assert closed_list["items"][0]["tradeId"] == trade_id
    assert client.get("/api/v1/paper-trades", params={"symbol": "ETHUSDT"}).json()[
        "items"
    ][0]["status"] == "CANCELLED"


def test_rejects_duplicate_unsafe_invalid_and_unknown_paper_trades() -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    setup = create_setup(client)
    setup_id = str(setup["eventId"])
    create_trade(client, setup_id)
    duplicate = client.post(
        "/api/v1/paper-trades",
        json={"setupId": setup_id, "accountBalance": 10_000, "riskPercent": 1},
    )
    assert duplicate.status_code == 409

    unsafe_payload = deepcopy(valid_payload())
    unsafe_payload["eventId"] = "BTCUSDT-1-unsafe-paper"
    create_setup(client, **unsafe_payload)
    unsafe = client.post(
        "/api/v1/paper-trades",
        json={
            "setupId": unsafe_payload["eventId"],
            "accountBalance": 10_000,
            "riskPercent": 2,
        },
    )
    assert unsafe.status_code == 422
    assert "RISK_PER_TRADE_EXCEEDED" in unsafe.json()["detail"]

    missing = str(uuid4())
    assert client.get(f"/api/v1/paper-trades/{missing}").status_code == 404
    assert client.get(f"/api/v1/paper-trades/{missing}/events").status_code == 404
    assert client.post(
        "/api/v1/paper-trades",
        json={"setupId": "missing-setup", "accountBalance": 10_000, "riskPercent": 1},
    ).status_code == 404
    assert client.post(
        "/api/v1/paper-trades",
        json={"setupId": setup_id, "accountBalance": 0, "riskPercent": 0},
    ).status_code == 422


def test_short_trade_closes_at_stop_loss() -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    payload = valid_payload(
        event_id="BTCUSDT-1-paper-short",
        htf_bias="BEARISH",
    )
    payload["direction"] = "SHORT"
    payload["execution"] = {
        "entry": 100,
        "stopLoss": 105,
        "takeProfit": 90,
        "riskReward": 2,
    }
    setup = create_setup(client, **payload)
    trade = create_trade(client, str(setup["eventId"]))
    trade_id = trade["tradeId"]

    opened = client.post(
        f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 100}
    )
    assert opened.json()["status"] == "OPEN"
    stopped = client.post(
        f"/api/v1/paper-trades/{trade_id}/market-price", json={"price": 106}
    )

    assert stopped.status_code == 200
    assert stopped.json()["exitReason"] == "STOP_LOSS"
    assert stopped.json()["exitPrice"] == 105
    assert stopped.json()["realizedR"] == -1
    last_event = client.get(f"/api/v1/paper-trades/{trade_id}/events").json()["items"][-1]
    assert last_event["details"]["marketPrice"] == 106
    assert last_event["details"]["exitReason"] == "STOP_LOSS"


def test_terminal_paper_trade_updates_existing_journal() -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    setup = create_setup(client, eventId="BTCUSDT-1-paper-journal")
    setup_id = str(setup["eventId"])
    trade = create_trade(client, setup_id)
    journal_response = client.post(
        f"/api/v1/setups/{setup_id}/journal",
        json={"executionStatus": "TAKEN"},
    )
    assert journal_response.status_code == 201, journal_response.text
    journal = journal_response.json()
    assert journal["outcomeId"] is None

    assert client.post(
        f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
        json={"price": 65180},
    ).json()["status"] == "OPEN"
    closed = client.post(
        f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
        json={"price": 65580},
    ).json()

    updated = client.get(f"/api/v1/journal/{journal['journalId']}").json()
    assert updated["revision"] == 2
    assert updated["outcomeId"] == closed["outcomeId"]
    assert updated["outcomeLabel"] == "WIN"
    assert updated["realizedR"] == 2
    assert updated["outcomeSnapshot"]["engine_version"] == "paper-execution-v1"


def test_paper_outcome_notification_is_emitted_only_once(caplog) -> None:
    client = TestClient(
        create_app(
            Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
        )
    )
    setup = create_setup(client, eventId="BTCUSDT-1-paper-notification")
    trade = create_trade(client, str(setup["eventId"]))

    with caplog.at_level("INFO", logger="uvicorn.error"):
        client.post(
            f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
            json={"price": 65180},
        )
        closed = client.post(
            f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
            json={"price": 65580},
        )
        assert closed.status_code == 200
        assert client.post("/api/v1/outcomes/paper-trades/reconcile").status_code == 200

    notifications = [
        record for record in caplog.records if record.message == "paper_outcome_notification"
    ]
    assert len(notifications) == 1


def test_notification_failure_does_not_fail_terminal_trade(caplog) -> None:
    class FailingNotificationAdapter:
        enabled = True

        def send_paper_outcome(self, notification: object) -> None:
            del notification
            raise RuntimeError("notification unavailable")

    app = create_app(
        Settings(webhook_event_repository="memory", paper_auto_trade_enabled=False)
    )
    app.state.paper_trade_outcome_service._notifications = FailingNotificationAdapter()
    client = TestClient(app)
    setup = create_setup(client, eventId="BTCUSDT-1-paper-notification-failure")
    trade = create_trade(client, str(setup["eventId"]))
    client.post(
        f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
        json={"price": 65180},
    )

    with caplog.at_level("ERROR", logger="smc_assistant.application.paper_trade_outcomes"):
        closed = client.post(
            f"/api/v1/paper-trades/{trade['tradeId']}/market-price",
            json={"price": 65580},
        )

    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"
    assert closed.json()["outcomeLabel"] == "WIN"
    assert "paper_outcome_notification_failed" in caplog.text


def test_concurrent_creations_respect_maximum_open_position_limit() -> None:
    app = create_app(
        Settings(
            webhook_event_repository="memory",
            paper_max_open_positions=1,
            paper_auto_trade_enabled=False,
        )
    )
    with TestClient(app) as client:
        first = create_setup(client, eventId="BTCUSDT-1-paper-concurrent")
        second = create_setup(
            client,
            eventId="ETHUSDT-1-paper-concurrent",
            symbol="ETHUSDT",
        )

        def submit(setup_id: object):
            return client.post(
                "/api/v1/paper-trades",
                json={"setupId": setup_id, "accountBalance": 10_000, "riskPercent": 1},
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(submit, [first["eventId"], second["eventId"]]))

    assert sorted(response.status_code for response in responses) == [201, 422]
    rejected = next(response for response in responses if response.status_code == 422)
    assert "MAX_OPEN_POSITIONS" in rejected.json()["detail"]
