from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol

from smc_assistant.application.audit import (
    AuditEventType,
    AuditLogger,
    NoopAuditLogger,
    create_audit_event,
)
from smc_assistant.application.setup_candidates import (
    SetupCandidateRepository,
    setup_candidate_from_tradingview_payload,
)
from smc_assistant.application.setup_scoring import score_tradingview_payload
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.setup_scoring import SetupScore, SetupScoringConfig


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
    setup_candidate_id: str
    setup_score: SetupScore
    message: str


class WebhookIngestionService:
    def __init__(
        self,
        repository: WebhookEventRepository,
        audit_logger: AuditLogger | None = None,
        scoring_config: SetupScoringConfig | None = None,
        setup_candidate_repository: SetupCandidateRepository | None = None,
    ) -> None:
        self._repository = repository
        self._audit_logger = audit_logger or NoopAuditLogger()
        self._scoring_config = scoring_config
        self._setup_candidate_repository = setup_candidate_repository

    def ingest_tradingview(
        self,
        payload: TradingViewWebhookPayload,
        *,
        received_at: datetime | None = None,
    ) -> WebhookIngestionResult:
        event_received_at = received_at or datetime.now(UTC)
        setup_score = score_tradingview_payload(payload, self._scoring_config)
        setup_candidate = setup_candidate_from_tradingview_payload(
            payload,
            setup_score,
            received_at=event_received_at,
        )
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
            if self._setup_candidate_repository is not None:
                self._setup_candidate_repository.save_if_absent(setup_candidate)

            self._audit_logger.record(
                create_audit_event(
                    AuditEventType.WEBHOOK_ACCEPTED,
                    {
                        "event_id": record.event_id,
                        "event_type": record.event_type,
                        "source": record.source,
                        "schema_version": record.schema_version,
                        "setup_score": setup_score.score,
                        "setup_accepted": setup_score.accepted,
                        "scoring_config_version": setup_score.config_version,
                        "setup_candidate_id": setup_candidate.setup_id,
                    },
                    occurred_at=record.received_at,
                )
            )
            return WebhookIngestionResult(
                status=WebhookIngestionStatus.ACCEPTED,
                event_id=record.event_id,
                event_type=record.event_type,
                schema_version=record.schema_version,
                received_at=record.received_at,
                first_received_at=record.received_at,
                setup_candidate_id=setup_candidate.setup_id,
                setup_score=setup_score,
                message="TradingView webhook payload accepted for processing.",
            )

        existing_record = save_result.record
        existing_payload = TradingViewWebhookPayload.model_validate(existing_record.payload)
        existing_setup_score = score_tradingview_payload(existing_payload, self._scoring_config)
        existing_setup_candidate = setup_candidate_from_tradingview_payload(
            existing_payload,
            existing_setup_score,
            received_at=existing_record.received_at,
        )
        self._audit_logger.record(
            create_audit_event(
                AuditEventType.WEBHOOK_DUPLICATE,
                {
                    "event_id": existing_record.event_id,
                    "event_type": existing_record.event_type,
                    "source": existing_record.source,
                    "schema_version": existing_record.schema_version,
                    "first_received_at": existing_record.received_at.isoformat(),
                    "setup_score": existing_setup_score.score,
                    "setup_accepted": existing_setup_score.accepted,
                    "scoring_config_version": existing_setup_score.config_version,
                    "setup_candidate_id": existing_setup_candidate.setup_id,
                },
                occurred_at=event_received_at,
            )
        )
        return WebhookIngestionResult(
            status=WebhookIngestionStatus.DUPLICATE,
            event_id=existing_record.event_id,
            event_type=existing_record.event_type,
            schema_version=existing_record.schema_version,
            received_at=event_received_at,
            first_received_at=existing_record.received_at,
            setup_candidate_id=existing_setup_candidate.setup_id,
            setup_score=existing_setup_score,
            message="TradingView webhook payload was already accepted.",
        )
