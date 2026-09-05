from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from smc_assistant.domain.candles import Candle, ensure_utc


@dataclass(frozen=True, slots=True)
class MarketDataQuery:
    symbol: str | None = None
    timeframe: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    def __post_init__(self) -> None:
        if self.start_time is not None:
            ensure_utc(self.start_time, "start_time")

        if self.end_time is not None:
            ensure_utc(self.end_time, "end_time")

        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time.")

    @property
    def normalized_symbol(self) -> str | None:
        if self.symbol is None or self.symbol.strip() == "":
            return None

        return self.symbol.strip().upper()


@runtime_checkable
class MarketDataProvider(Protocol):
    def load_candles(self, query: MarketDataQuery | None = None) -> tuple[Candle, ...]:
        pass
