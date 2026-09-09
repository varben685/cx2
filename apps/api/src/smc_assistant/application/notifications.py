from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from smc_assistant.domain.enums import TradeOutcomeLabel


@dataclass(frozen=True, slots=True)
class PaperOutcomeNotification:
    outcome_id: UUID
    trade_id: UUID
    setup_id: str
    symbol: str
    label: TradeOutcomeLabel
    realized_r: float | None
    occurred_at: datetime


class NotificationAdapter(Protocol):
    enabled: bool

    def send_paper_outcome(self, notification: PaperOutcomeNotification) -> None:
        pass


class NoopNotificationAdapter:
    enabled = False

    def send_paper_outcome(self, notification: PaperOutcomeNotification) -> None:
        del notification
