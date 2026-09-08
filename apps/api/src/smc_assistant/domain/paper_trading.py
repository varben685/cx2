from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from math import isfinite
from typing import Any
from uuid import UUID


class PaperTradeStatus(StrEnum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class PaperTradeExitReason(StrEnum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    MANUAL = "MANUAL"
    CANCELLED = "CANCELLED"


class PaperTradeEventType(StrEnum):
    CREATED = "CREATED"
    PRICE_OBSERVED = "PRICE_OBSERVED"
    OPENED = "OPENED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class PaperTrade:
    trade_id: UUID
    setup_id: str
    event_id: str
    symbol: str
    exchange: str
    timeframe: str
    direction: str
    session: str
    strategy_version: str
    status: PaperTradeStatus
    entry_price: float
    stop_loss: float
    take_profit: float
    planned_risk_reward: float
    account_balance: float
    risk_percent: float
    risk_amount: float
    quantity: float
    opened_at: datetime | None
    closed_at: datetime | None
    exit_price: float | None
    exit_reason: PaperTradeExitReason | None
    realized_pnl: float | None
    realized_r: float | None
    risk_policy_version: str
    created_at: datetime
    updated_at: datetime
    revision: int

    def __post_init__(self) -> None:
        for value in (self.created_at, self.updated_at, self.opened_at, self.closed_at):
            if value is not None and value.utcoffset() is None:
                raise ValueError("Paper trade timestamps must be timezone-aware.")
        if self.revision < 1:
            raise ValueError("Paper trade revision must be positive.")
        sizing_values = (
            self.entry_price,
            self.stop_loss,
            self.take_profit,
            self.account_balance,
            self.risk_percent,
            self.risk_amount,
            self.quantity,
        )
        if not all(isfinite(value) and value > 0 for value in sizing_values):
            raise ValueError("Paper trade prices and sizing values must be positive.")
        if self.direction not in {"LONG", "SHORT"}:
            raise ValueError("Paper trade direction must be LONG or SHORT.")
        if self.status == PaperTradeStatus.PENDING and self.opened_at is not None:
            raise ValueError("Pending paper trade cannot have an open timestamp.")
        if self.status == PaperTradeStatus.OPEN and self.opened_at is None:
            raise ValueError("Open paper trade requires an open timestamp.")
        if self.status == PaperTradeStatus.CLOSED and any(
            value is None
            for value in (
                self.opened_at,
                self.closed_at,
                self.exit_price,
                self.exit_reason,
                self.realized_pnl,
                self.realized_r,
            )
        ):
            raise ValueError("Closed paper trade requires complete execution results.")
        if self.status == PaperTradeStatus.CANCELLED and (
            self.closed_at is None or self.exit_reason != PaperTradeExitReason.CANCELLED
        ):
            raise ValueError("Cancelled paper trade requires cancellation metadata.")


@dataclass(frozen=True, slots=True)
class PaperTradeEvent:
    trade_id: UUID
    sequence: int
    event_type: PaperTradeEventType
    occurred_at: datetime
    details: dict[str, Any]

    def __post_init__(self) -> None:
        if self.sequence < 1:
            raise ValueError("Paper trade event sequence must be positive.")
        if self.occurred_at.utcoffset() is None:
            raise ValueError("Paper trade event timestamp must be timezone-aware.")
