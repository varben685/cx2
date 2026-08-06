from enum import StrEnum


class TradeDirection(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


class TradeOutcomeLabel(StrEnum):
    WIN = "WIN"
    LOSS = "LOSS"
    BREAK_EVEN = "BREAK_EVEN"
    TIMEOUT = "TIMEOUT"
    CANCELLED = "CANCELLED"
    INVALIDATED = "INVALIDATED"
    NOT_TRIGGERED = "NOT_TRIGGERED"

