from datetime import UTC, datetime

from sqlalchemy import Engine, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.webhook_ingestion import (
    WebhookEventRecord,
    WebhookEventSaveResult,
)
from smc_assistant.infrastructure.webhook_event_schema import webhook_events


class SQLWebhookEventRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_if_absent(self, record: WebhookEventRecord) -> WebhookEventSaveResult:
        existing_record = self.get_by_event_id(record.event_id)
        if existing_record is not None:
            return WebhookEventSaveResult(record=existing_record, created=False)

        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(webhook_events).values(
                        event_id=record.event_id,
                        event_type=record.event_type,
                        source=record.source,
                        schema_version=record.schema_version,
                        payload=record.payload,
                        received_at=record.received_at,
                        created_at=datetime.now(UTC),
                    )
                )
        except IntegrityError:
            duplicated_record = self.get_by_event_id(record.event_id)
            if duplicated_record is None:
                raise
            return WebhookEventSaveResult(record=duplicated_record, created=False)

        return WebhookEventSaveResult(record=record, created=True)

    def get_by_event_id(self, event_id: str) -> WebhookEventRecord | None:
        query = select(
            webhook_events.c.event_id,
            webhook_events.c.event_type,
            webhook_events.c.source,
            webhook_events.c.schema_version,
            webhook_events.c.payload,
            webhook_events.c.received_at,
        ).where(webhook_events.c.event_id == event_id)

        with self._engine.connect() as connection:
            row = connection.execute(query).mappings().one_or_none()

        if row is None:
            return None

        return _record_from_row(row)


def _record_from_row(row: RowMapping) -> WebhookEventRecord:
    received_at = row["received_at"]
    if not isinstance(received_at, datetime):
        msg = "webhook_events.received_at must be a datetime"
        raise TypeError(msg)
    if received_at.tzinfo is None:
        received_at = received_at.replace(tzinfo=UTC)

    return WebhookEventRecord(
        event_id=str(row["event_id"]),
        event_type=str(row["event_type"]),
        source=str(row["source"]),
        schema_version=str(row["schema_version"]),
        payload=dict(row["payload"]),
        received_at=received_at,
    )
