import logging

from smc_assistant.application.audit import AuditEvent, AuditLogger


class StructuredAuditLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("smc_assistant.audit")

    def record(self, event: AuditEvent) -> None:
        self._logger.info(
            "audit_event",
            extra={
                "audit_event_type": event.event_type,
                "audit_occurred_at": event.occurred_at.isoformat(),
                "audit_metadata": event.metadata,
            },
        )


def create_audit_logger() -> AuditLogger:
    return StructuredAuditLogger()
