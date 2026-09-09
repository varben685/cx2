import logging

from smc_assistant.application.notifications import (
    NoopNotificationAdapter,
    NotificationAdapter,
    PaperOutcomeNotification,
)


class LoggingNotificationAdapter:
    enabled = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("uvicorn.error")

    def send_paper_outcome(self, notification: PaperOutcomeNotification) -> None:
        self._logger.info(
            "paper_outcome_notification",
            extra={
                "outcome_id": str(notification.outcome_id),
                "trade_id": str(notification.trade_id),
                "setup_id": notification.setup_id,
                "symbol": notification.symbol,
                "label": notification.label.value,
                "realized_r": notification.realized_r,
                "occurred_at": notification.occurred_at.isoformat(),
            },
        )


def create_notification_adapter(kind: str) -> NotificationAdapter:
    if kind == "log":
        return LoggingNotificationAdapter()
    return NoopNotificationAdapter()
