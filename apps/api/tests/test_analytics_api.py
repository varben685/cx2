from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from test_outcome_records import save_example

from smc_assistant.config import Settings
from smc_assistant.main import create_app


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_summary_reads_saved_outcomes_from_configured_repository(backend, tmp_path):
    settings = Settings(
        webhook_event_repository="postgres" if backend == "sqlite" else "memory",
        database_url=f"sqlite+pysqlite:///{tmp_path / 'analytics.db'}",
    )
    app = create_app(settings)
    first = save_example(app.state.outcome_repository).record
    eth = replace(
        first,
        outcome_id=uuid4(),
        evaluation=replace(first.evaluation, event_id="eth-event", symbol="ETHUSDT"),
    )
    app.state.outcome_repository.save_if_absent(eth)
    save_example(app.state.outcome_repository)
    if backend == "sqlite":
        app = create_app(settings)

    with TestClient(app) as client:
        response = client.get("/api/v1/analytics/summary", params={"runId": str(first.run_id)})
        assert response.status_code == 200
        data = response.json()
        assert data["runId"] == str(first.run_id)
        assert data["symbol"] is None
        assert data["statistics"]["totalSetups"] == 2
        assert data["statistics"]["totalNetR"] == 3.874
        assert data["statistics"]["netWinRate"] == 1
        assert data["statistics"]["netProfitFactor"] is None
        assert data["statistics"]["outcomeCounts"]["WIN"] == 2

        filtered = client.get(
            "/api/v1/analytics/summary",
            params={"runId": str(first.run_id), "symbol": "ETHUSDT"},
        )
        assert filtered.json()["statistics"]["closedTrades"] == 1
        assert filtered.json()["symbol"] == "ETHUSDT"


def test_unknown_run_and_empty_filter_return_empty_statistics():
    app = create_app(Settings(webhook_event_repository="memory"))
    first = save_example(app.state.outcome_repository).record
    with TestClient(app) as client:
        for params in (
            {"runId": str(uuid4())},
            {"runId": str(first.run_id), "symbol": "missing"},
        ):
            response = client.get("/api/v1/analytics/summary", params=params)
            assert response.status_code == 200
            stats = response.json()["statistics"]
            assert stats["totalSetups"] == 0
            assert stats["netWinRate"] is None
            assert stats["netExpectancyR"] is None
            assert stats["netProfitFactor"] is None


@pytest.mark.parametrize(
    "params", [{}, {"runId": "invalid"}, {"runId": str(uuid4()), "symbol": ""}]
)
def test_rejects_missing_run_or_invalid_filters(params):
    with TestClient(create_app(Settings(webhook_event_repository="memory"))) as client:
        assert client.get("/api/v1/analytics/summary", params=params).status_code == 422
