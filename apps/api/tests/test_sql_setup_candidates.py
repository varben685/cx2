from dataclasses import replace
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine

from smc_assistant.application.setup_candidates import SetupCandidateRecord
from smc_assistant.application.webhook_ingestion import WebhookEventRecord
from smc_assistant.infrastructure.sql_setup_candidates import SQLSetupCandidateRepository
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository
from smc_assistant.infrastructure.webhook_event_schema import metadata


def create_repositories() -> tuple[SQLWebhookEventRepository, SQLSetupCandidateRepository]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    return SQLWebhookEventRepository(engine), SQLSetupCandidateRepository(engine)


def webhook_record(
    *,
    event_id: str = "BTCUSDT-1-1767225660000-LONG",
    received_at: datetime | None = None,
) -> WebhookEventRecord:
    return WebhookEventRecord(
        event_id=event_id,
        event_type="SETUP_CANDIDATE",
        source="TRADINGVIEW",
        schema_version="1.0",
        payload={"eventId": event_id, "symbol": "BTCUSDT"},
        received_at=received_at or datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
    )


def setup_candidate_record(
    *,
    event_id: str = "BTCUSDT-1-1767225660000-LONG",
    score: float = 88.5,
    received_at: datetime | None = None,
) -> SetupCandidateRecord:
    record_received_at = received_at or datetime(2026, 9, 3, 10, 0, tzinfo=UTC)
    return SetupCandidateRecord(
        setup_id=event_id,
        event_id=event_id,
        schema_version="1.0",
        strategy_version="smc-rce-v1",
        scoring_config_version="rule-score-v1",
        symbol="BTCUSDT",
        exchange="BINANCE",
        timeframe="1",
        direction="LONG",
        htf_bias="BULLISH",
        score=score,
        accepted=True,
        components=[
            {
                "name": "HTF_BIAS",
                "score": 20.0,
                "maxScore": 20.0,
                "reason": "HTF bias aligns with setup direction.",
            }
        ],
        rejection_reasons=[],
        positive_reasons=["HTF bias aligns with setup direction."],
        negative_reasons=[],
        bar_close_time=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
        received_at=record_received_at,
    )


def test_sql_setup_candidate_repository_saves_and_loads_record() -> None:
    webhook_repository, setup_repository = create_repositories()
    webhook = webhook_record()
    record = setup_candidate_record(event_id=webhook.event_id)
    webhook_repository.save_if_absent(webhook)

    result = setup_repository.save_if_absent(record)

    assert result.created is True
    assert setup_repository.get_by_event_id(webhook.event_id) == record


def test_sql_setup_candidate_repository_is_idempotent_by_event_id() -> None:
    webhook_repository, setup_repository = create_repositories()
    webhook = webhook_record()
    first_record = setup_candidate_record(event_id=webhook.event_id, score=88.5)
    second_record = setup_candidate_record(
        event_id=webhook.event_id,
        score=42.0,
        received_at=first_record.received_at + timedelta(seconds=30),
    )
    webhook_repository.save_if_absent(webhook)

    first_result = setup_repository.save_if_absent(first_record)
    second_result = setup_repository.save_if_absent(second_record)

    assert first_result.created is True
    assert second_result.created is False
    assert second_result.record == first_record
    assert setup_repository.get_by_event_id(webhook.event_id) == first_record


def test_sql_setup_candidate_repository_returns_none_for_unknown_event_id() -> None:
    _, setup_repository = create_repositories()

    assert setup_repository.get_by_event_id("missing-event-id") is None


def test_sql_setup_candidate_repository_gets_by_setup_id() -> None:
    webhook_repository, setup_repository = create_repositories()
    webhook = webhook_record()
    record = setup_candidate_record(event_id=webhook.event_id)
    webhook_repository.save_if_absent(webhook)
    setup_repository.save_if_absent(record)

    assert setup_repository.get_by_setup_id(record.setup_id) == record
    assert setup_repository.get_by_setup_id("missing-setup") is None


def test_sql_setup_candidate_repository_lists_recent_records_with_filters() -> None:
    webhook_repository, setup_repository = create_repositories()
    first_webhook = webhook_record(event_id="BTCUSDT-1-1767225660000-LONG")
    second_webhook = webhook_record(
        event_id="ETHUSDT-1-1767225720000-LONG",
        received_at=first_webhook.received_at + timedelta(minutes=1),
    )
    third_webhook = webhook_record(
        event_id="SOLUSDT-1-1767225780000-LONG",
        received_at=first_webhook.received_at + timedelta(minutes=2),
    )
    first_record = setup_candidate_record(event_id=first_webhook.event_id)
    second_record = setup_candidate_record(
        event_id=second_webhook.event_id,
        received_at=second_webhook.received_at,
    )
    second_record = replace(
        second_record,
        symbol="ETHUSDT",
    )
    third_record = setup_candidate_record(
        event_id=third_webhook.event_id,
        score=42.0,
        received_at=third_webhook.received_at,
    )
    third_record = replace(
        third_record,
        symbol="SOLUSDT",
        accepted=False,
    )

    for webhook in [first_webhook, second_webhook, third_webhook]:
        webhook_repository.save_if_absent(webhook)
    for record in [first_record, second_record, third_record]:
        setup_repository.save_if_absent(record)

    assert [record.symbol for record in setup_repository.list_recent(limit=2)] == [
        "SOLUSDT",
        "ETHUSDT",
    ]
    assert [record.symbol for record in setup_repository.list_recent(symbol="ETHUSDT")] == [
        "ETHUSDT"
    ]
    assert [record.symbol for record in setup_repository.list_recent(accepted=False)] == [
        "SOLUSDT"
    ]
