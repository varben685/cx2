from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload


class WebhookIngestionStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    DUPLICATE = "DUPLICATE"


@dataclass(frozen=True)
class WebhookEventRecord:
    event_id: str
    event_type: str
    source: str
    schema_version: str
    payload: dict[str, Any]
    received_at: datetime


@dataclass(frozen=True)
class WebhookEventSaveResult:
    record: WebhookEventRecord
    created: bool


class WebhookEventRepository(Protocol):
    def save_if_absent(self, record: WebhookEventRecord) -> WebhookEventSaveResult:
        pass


@dataclass(frozen=True)
class WebhookIngestionResult:
    status: WebhookIngestionStatus
    event_id: str
    event_type: str
    schema_version: str
    received_at: datetime
    first_received_at: datetime
    message: str


class WebhookIngestionService:
    def __init__(self, repository: WebhookEventRepository) -> None:
        self._repository = repository

    def ingest_tradingview(
        self,
        payload: TradingViewWebhookPayload,
        *,
        received_at: datetime | None = None,
    ) -> WebhookIngestionResult:
        event_received_at = received_at or datetime.now(UTC)
        record = WebhookEventRecord(
            event_id=payload.event_id,
            event_type=payload.event_type,
            source=payload.source,
            schema_version=payload.schema_version,
            payload=payload.model_dump(mode="json", by_alias=True),
            received_at=event_received_at,
        )

        save_result = self._repository.save_if_absent(record)
        if save_result.created:
            return WebhookIngestionResult(
                status=WebhookIngestionStatus.ACCEPTED,
                event_id=record.event_id,
                event_type=record.event_type,
                schema_version=record.schema_version,
                received_at=record.received_at,
                first_received_at=record.received_at,
                message="TradingView webhook payload accepted for processing.",
            )

        existing_record = save_result.record
        return WebhookIngestionResult(
            status=WebhookIngestionStatus.DUPLICATE,
            event_id=existing_record.event_id,
            event_type=existing_record.event_type,
            schema_version=existing_record.schema_version,
            received_at=event_received_at,
            first_received_at=existing_record.received_at,
            message="TradingView webhook payload was already accepted.",
        )
