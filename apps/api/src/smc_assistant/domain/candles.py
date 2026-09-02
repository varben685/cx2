from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


def ensure_utc(timestamp: datetime, field_name: str) -> datetime:
    if timestamp.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    if timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be expressed in UTC.")

    return timestamp.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class Candle:
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None

    def __post_init__(self) -> None:
        ensure_utc(self.open_time, "open_time")
        ensure_utc(self.close_time, "close_time")

        if self.close_time <= self.open_time:
            raise ValueError("close_time must be after open_time.")

        prices = {
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
        }
        for name, value in prices.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")

        if self.low > min(self.open, self.close):
            raise ValueError("low must be less than or equal to open and close.")

        if self.high < max(self.open, self.close):
            raise ValueError("high must be greater than or equal to open and close.")

        if self.low > self.high:
            raise ValueError("low must be less than or equal to high.")

        if self.volume is not None and self.volume < 0:
            raise ValueError("volume must be non-negative when provided.")
