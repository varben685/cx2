from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

type AuditMetadataValue = str | int | float | bool | None


class AuditEventType(StrEnum):
    WEBHOOK_ACCEPTED = "WEBHOOK_ACCEPTED"
    WEBHOOK_DUPLICATE = "WEBHOOK_DUPLICATE"
    WEBHOOK_VALIDATION_FAILED = "WEBHOOK_VALIDATION_FAILED"


@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    occurred_at: datetime
    metadata: dict[str, AuditMetadataValue]


@runtime_checkable
class AuditLogger(Protocol):
    def record(self, event: AuditEvent) -> None:
        pass


class NoopAuditLogger:
    def record(self, event: AuditEvent) -> None:
        del event


def create_audit_event(
    event_type: AuditEventType,
    metadata: dict[str, AuditMetadataValue],
    *,
    occurred_at: datetime | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type=event_type,
        occurred_at=occurred_at or datetime.now(UTC),
        metadata=metadata,
    )
