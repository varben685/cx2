from copy import deepcopy
from uuid import uuid4

from fastapi.testclient import TestClient
from test_backtests_api import backtest_payload

from smc_assistant.main import create_app


def create_setup(client: TestClient, payload: dict[str, object] | None = None) -> dict[str, object]:
    backtest = backtest_payload()
    setup = payload or backtest["setups"][0]
    response = client.post("/api/v1/webhooks/tradingview", json=setup)
    assert response.status_code == 202
    return setup


def journal_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "executionStatus": "TAKEN",
        "userNote": "Waited for confirmation.",
        "screenshotReference": "screenshots/btc-long.png",
        "manualRating": 4,
        "manualOverride": True,
        "overrideReason": "The lower timeframe confirmed the entry.",
        "tags": ["A+", "London"],
    }
    payload.update(changes)
    return payload


def test_creates_lists_reads_updates_and_versions_journal() -> None:
    client = TestClient(create_app())
    setup = create_setup(client)
    setup_id = str(setup["eventId"])

    created_response = client.post(
        f"/api/v1/setups/{setup_id}/journal",
        json=journal_payload(),
    )

    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    assert created["setupId"] == setup_id
    assert created["symbol"] == "BTCUSDT"
    assert created["session"] == "NEW_YORK"
    assert created["executionStatus"] == "TAKEN"
    assert created["revision"] == 1
    assert created["outcomeId"] is None
    assert created["setupSnapshot"]["sourcePayload"]["eventId"] == setup_id

    listed = client.get("/api/v1/journal", params={"executionStatus": "TAKEN"}).json()
    assert listed["count"] == 1
    assert "setupSnapshot" not in listed["items"][0]
    assert client.get(f"/api/v1/journal/{created['journalId']}").json() == created

    update = journal_payload(
        expectedRevision=1,
        executionStatus="SKIPPED",
        userNote="Skipped after the confirmation failed.",
        manualOverride=False,
        overrideReason=None,
        tags=["discipline", "Discipline"],
    )
    updated_response = client.put(
        f"/api/v1/journal/{created['journalId']}", json=update
    )
    assert updated_response.status_code == 200
    updated = updated_response.json()
    assert updated["executionStatus"] == "SKIPPED"
    assert updated["revision"] == 2
    assert updated["tags"] == ["discipline"]
    assert updated["setupSnapshot"] == created["setupSnapshot"]

    stale_response = client.put(
        f"/api/v1/journal/{created['journalId']}", json=update
    )
    assert stale_response.status_code == 409
    revisions = client.get(
        f"/api/v1/journal/{created['journalId']}/revisions"
    ).json()
    assert revisions["count"] == 2
    assert [item["revision"] for item in revisions["items"]] == [1, 2]


def test_automatically_links_latest_matching_outcome() -> None:
    client = TestClient(create_app())
    payload = backtest_payload()
    setup = create_setup(client, payload["setups"][0])
    backtest_response = client.post("/api/v1/backtests", json=payload)
    assert backtest_response.status_code == 201

    response = client.post(
        f"/api/v1/setups/{setup['eventId']}/journal",
        json=journal_payload(manualOverride=False, overrideReason=None),
    )

    assert response.status_code == 201, response.text
    journal = response.json()
    assert journal["outcomeId"] == backtest_response.json()["outcomeIds"][0]
    assert journal["outcomeLabel"] == "WIN"
    assert journal["realizedR"] == 1.937
    assert journal["mfeR"] == 2.2
    assert journal["maeR"] == -0.2
    assert journal["outcomeSnapshot"] is not None


def test_rejects_duplicate_missing_mismatched_and_invalid_journal() -> None:
    client = TestClient(create_app())
    setup = create_setup(client)
    setup_id = str(setup["eventId"])
    valid = journal_payload(manualOverride=False, overrideReason=None)
    assert client.post(f"/api/v1/setups/{setup_id}/journal", json=valid).status_code == 201
    assert client.post(f"/api/v1/setups/{setup_id}/journal", json=valid).status_code == 409
    assert client.post("/api/v1/setups/missing/journal", json=valid).status_code == 404

    invalid = deepcopy(valid)
    invalid.update(manualOverride=True, overrideReason=" ")
    assert client.post(f"/api/v1/setups/{setup_id}/journal", json=invalid).status_code == 422
    assert client.get("/api/v1/journal", params={"limit": 0}).status_code == 422
    assert client.get(f"/api/v1/journal/{uuid4()}").status_code == 404

    other_setup = deepcopy(backtest_payload()["setups"][0])
    other_setup["eventId"] = "other-journal-event"
    other_backtest = backtest_payload()
    other_backtest["runId"] = str(uuid4())
    other_backtest["setups"] = [other_setup]
    assert client.post("/api/v1/backtests", json=other_backtest).status_code == 201
    outcome_id = client.get(
        "/api/v1/outcomes", params={"runId": other_backtest["runId"]}
    ).json()["items"][0]["outcomeId"]
    second_setup = deepcopy(setup)
    second_setup["eventId"] = "second-journal-setup"
    create_setup(client, second_setup)
    mismatch = journal_payload(
        outcomeId=outcome_id,
        manualOverride=False,
        overrideReason=None,
    )
    response = client.post("/api/v1/setups/second-journal-setup/journal", json=mismatch)
    assert response.status_code == 422
    assert response.json()["detail"] == "Outcome does not belong to the selected setup."
