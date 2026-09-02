from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine

from smc_assistant.application.webhook_ingestion import WebhookEventRecord
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository
from smc_assistant.infrastructure.webhook_event_schema import metadata


def create_repository() -> SQLWebhookEventRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    metadata.create_all(engine)
    return SQLWebhookEventRepository(engine)


def webhook_record(
    *,
    event_id: str = "BTCUSDT-1m-1720000000-bullish-choch",
    symbol: str = "BTCUSDT",
    received_at: datetime | None = None,
) -> WebhookEventRecord:
    return WebhookEventRecord(
        event_id=event_id,
        event_type="SETUP_CANDIDATE",
        source="TRADINGVIEW",
        schema_version="1.0",
        payload={"eventId": event_id, "symbol": symbol},
        received_at=received_at or datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
    )


def test_sql_repository_saves_new_webhook_event() -> None:
    repository = create_repository()
    record = webhook_record()

    result = repository.save_if_absent(record)

    assert result.created is True
    assert result.record == record
    assert repository.get_by_event_id(record.event_id) == record


def test_sql_repository_returns_existing_record_for_duplicate_event_id() -> None:
    repository = create_repository()
    first_record = webhook_record(symbol="BTCUSDT")
    second_record = webhook_record(
        symbol="ETHUSDT",
        received_at=first_record.received_at + timedelta(seconds=30),
    )

    first_result = repository.save_if_absent(first_record)
    second_result = repository.save_if_absent(second_record)

    assert first_result.created is True
    assert second_result.created is False
    assert second_result.record == first_record
    assert repository.get_by_event_id(first_record.event_id) == first_record


def test_sql_repository_returns_none_for_unknown_event_id() -> None:
    repository = create_repository()

    assert repository.get_by_event_id("missing-event-id") is None
