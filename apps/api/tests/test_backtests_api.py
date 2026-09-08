import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from test_outcome_evaluation import valid_payload
from test_outcome_records import repository as repository
from test_outcome_records import save_example

from smc_assistant.config import Settings
from smc_assistant.infrastructure.in_memory_backtests import InMemoryBacktestRepository
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository
from smc_assistant.infrastructure.sql_backtests import SQLBacktestRepository
from smc_assistant.main import create_app


def backtest_payload():
    return {
        "runId": str(uuid4()),
        "setups": [valid_payload().model_dump(mode="json", by_alias=True)],
        "candlesCsv": (
            "symbol,timeframe,time,open,high,low,close,volume\n"
            "BTCUSDT,1,2026-01-01T12:00:00Z,100,112,90,100,1000\n"
            "BTCUSDT,1,2026-01-01T12:01:00Z,100,101,99,100,1000\n"
            "BTCUSDT,1,2026-01-01T12:02:00Z,100,111,99,110,1000\n"
        ),
        "config": {"commissionBpsPerSide": 10, "slippageBpsPerSide": 5},
    }


@pytest.fixture
def client(repository):
    app = create_app(Settings(webhook_event_repository="memory"))
    app.state.outcome_repository = repository
    app.state.backtest_repository = (
        InMemoryBacktestRepository(repository)
        if isinstance(repository, InMemoryOutcomeRepository)
        else SQLBacktestRepository(repository._engine)
    )
    with TestClient(app) as client:
        yield client


def test_create_read_outcomes_and_analytics(client):
    payload = backtest_payload()
    response = client.post("/api/v1/backtests", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["runId"] == payload["runId"]
    assert body["statistics"]["totalNetR"] == 1.937
    assert body["config"]["maxHoldingBars"] == 30
    assert "candlesCsv" not in response.text
    assert client.get(f"/api/v1/backtests/{payload['runId']}").json() == body
    assert client.get("/api/v1/backtests").json()["items"] == [body]
    outcomes = client.get("/api/v1/outcomes", params={"runId": payload["runId"]}).json()
    assert outcomes["count"] == 1
    record = outcomes["items"][0]
    assert record["outcome"]["label"] == "WIN"
    assert record["outcome"]["costs"]["costR"] == 0.063
    assert record["outcome"]["excursion"]["mfeR"] == 2.2
    assert record["outcomeId"] == body["outcomeIds"][0]
    assert client.get(f"/api/v1/outcomes/{record['outcomeId']}").json() == record
    assert (
        client.get("/api/v1/analytics/summary", params={"runId": payload["runId"]}).json()[
            "statistics"
        ]
        == body["statistics"]
    )
    report_response = client.get(
        "/api/v1/analytics/report", params={"runId": payload["runId"]}
    )
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["risk"]["averageWinR"] == 1.937
    assert report["risk"]["maximumDrawdownR"] == 0
    assert report["equityCurve"][0]["cumulativeNetR"] == 1.937
    assert report["bySession"][0]["label"] == "NEW_YORK"
    assert report["byScoreBucket"][0]["statistics"]["closedTrades"] == 1
    assert report["decisions"]["journaledSetups"] == 0
    by_session = client.get(
        "/api/v1/analytics/by-session", params={"runId": payload["runId"]}
    ).json()
    assert by_session["items"] == report["bySession"]
    by_score = client.get(
        "/api/v1/analytics/by-score-bucket", params={"runId": payload["runId"]}
    ).json()
    assert by_score["items"] == report["byScoreBucket"]
    # A new SQL adapter must restore the complete typed input and result snapshot.
    stored = client.app.state.backtest_repository.get(UUID(payload["runId"]))
    assert stored.request.candles_csv == payload["candlesCsv"]


def test_retry_returns_original_and_changed_input_conflicts(client):
    payload = backtest_payload()
    first = client.post("/api/v1/backtests", json=payload)
    replay = client.post("/api/v1/backtests", json=payload)
    assert replay.status_code == 200
    assert replay.json() == first.json()
    changed = deepcopy(payload)
    changed["config"]["commissionBpsPerSide"] = 0
    assert client.post("/api/v1/backtests", json=changed).status_code == 409
    changed["runId"] = str(uuid4())
    assert client.post("/api/v1/backtests", json=changed).status_code == 201
    assert client.get("/api/v1/backtests").json()["count"] == 2
    assert client.get("/api/v1/outcomes", params={"runId": payload["runId"]}).json()["count"] == 1


def test_later_incomplete_setup_leaves_no_partial_run(client):
    payload = backtest_payload()
    second = deepcopy(payload["setups"][0])
    second.update(
        eventId="later-event-id",
        barOpenTime="2026-01-01T13:00:00Z",
        barCloseTime="2026-01-01T13:01:00Z",
    )
    payload["setups"].append(second)
    response = client.post("/api/v1/backtests", json=payload)
    assert response.status_code == 422
    assert "Not enough candles" in response.json()["detail"]
    assert client.get(f"/api/v1/backtests/{payload['runId']}").status_code == 404
    assert client.get("/api/v1/outcomes", params={"runId": payload["runId"]}).json()["count"] == 0
    payload["setups"].pop()
    assert client.post("/api/v1/backtests", json=payload).status_code == 201


@pytest.mark.parametrize("change", ["duplicate", "market", "empty", "limit", "path", "config"])
def test_invalid_request_does_not_write(client, change):
    payload = backtest_payload()
    if change == "duplicate":
        payload["setups"] *= 2
    elif change == "market":
        second = deepcopy(payload["setups"][0])
        second.update(eventId="other-event-id", symbol="ETHUSDT")
        payload["setups"].append(second)
    elif change == "empty":
        payload["setups"] = []
    elif change == "limit":
        payload["candlesCsv"] = "x" * 1_000_001
    elif change == "path":
        payload["csvPath"] = "/tmp/private.csv"
    else:
        payload["config"]["maxHoldingBars"] = 0
    assert client.post("/api/v1/backtests", json=payload).status_code == 422
    assert client.get("/api/v1/backtests").json()["count"] == 0


@pytest.mark.parametrize(
    "csv_text",
    [
        "",
        "open,high,low,close\n1,2\n",
        "time,open,high,low,close\n2026-01-01T12:01:00Z,100,NaN,99,100\n",
        'time,open,high,low,close\n"unfinished',
        "time,open,open,low,close\n2026-01-01T12:01:00Z,100,101,99,100\n",
    ],
)
def test_bad_csv_returns_422(client, csv_text):
    payload = backtest_payload()
    payload["candlesCsv"] = csv_text
    assert client.post("/api/v1/backtests", json=payload).status_code == 422
    assert client.get("/api/v1/backtests").json()["count"] == 0


def test_nullable_untriggered_outcome(client):
    payload = backtest_payload()
    payload["setups"][0]["execution"].update(entry=200, stopLoss=195, takeProfit=210)
    payload["config"]["entryTimeoutBars"] = 2
    response = client.post("/api/v1/backtests", json=payload)
    assert response.status_code == 201
    record = client.get(f"/api/v1/outcomes/{response.json()['outcomeIds'][0]}").json()
    assert record["outcome"]["label"] == "NOT_TRIGGERED"
    assert record["outcome"]["excursion"] is None
    assert record["outcome"]["costs"] is None


def test_unknown_ids_and_filters(client):
    assert client.get(f"/api/v1/backtests/{uuid4()}").status_code == 404
    assert client.get(f"/api/v1/outcomes/{uuid4()}").status_code == 404
    assert client.get("/api/v1/backtests/not-a-uuid").status_code == 422
    assert client.get("/api/v1/outcomes").status_code == 422
    assert (
        client.get("/api/v1/analytics/report", params={"runId": str(uuid4())}).status_code
        == 404
    )
    assert client.get("/api/v1/backtests", params={"limit": 0}).status_code == 422


def test_existing_legacy_outcome_cannot_be_adopted(client):
    prior = save_example(client.app.state.outcome_repository).record
    payload = backtest_payload()
    payload["runId"] = str(prior.run_id)
    assert client.post("/api/v1/backtests", json=payload).status_code == 409
    assert client.get("/api/v1/backtests").json()["count"] == 0


def test_database_failure_rolls_back_run_and_outcomes(client):
    repository = client.app.state.outcome_repository
    if isinstance(repository, InMemoryOutcomeRepository):
        pytest.skip("SQL transaction rollback test")
    payload = backtest_payload()

    def fail_outcome_insert(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO") and "outcome_records" in statement:
            raise RuntimeError("Injected insert failure")

    event.listen(repository._engine, "before_cursor_execute", fail_outcome_insert)
    try:
        with pytest.raises(RuntimeError, match="Injected"):
            client.post("/api/v1/backtests", json=payload)
    finally:
        event.remove(repository._engine, "before_cursor_execute", fail_outcome_insert)
    assert client.get("/api/v1/backtests").json()["count"] == 0
    assert client.get("/api/v1/outcomes", params={"runId": payload["runId"]}).json()["count"] == 0


def test_concurrent_identical_requests_are_idempotent(client):
    repository = client.app.state.outcome_repository
    if (
        not isinstance(repository, InMemoryOutcomeRepository)
        and repository._engine.dialect.name == "sqlite"
    ):
        pytest.skip("Shared in-memory SQLite connection cannot run concurrent transactions")
    payload = backtest_payload()
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(
            executor.map(lambda _: client.post("/api/v1/backtests", json=payload), range(2))
        )
    assert sorted(response.status_code for response in responses) == [200, 201]
    assert responses[0].json() == responses[1].json()


def test_documented_example_is_executable(client):
    path = Path(__file__).resolve().parents[3] / "examples/backtests/demo-request.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    response = client.post("/api/v1/backtests", json=payload)
    assert response.status_code == 201
    assert response.json()["statistics"]["netExpectancyR"] == 1.937
