from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.candles import Candle


class FairValueGapKind(StrEnum):
    BULLISH_FVG = "BULLISH_FVG"
    BEARISH_FVG = "BEARISH_FVG"


@dataclass(frozen=True, slots=True)
class FairValueGapSettings:
    min_absolute_size: float = 0.0
    tick_size: float | None = None
    min_size_ticks: int | None = None

    def __post_init__(self) -> None:
        if self.min_absolute_size < 0:
            raise ValueError("min_absolute_size must be non-negative.")

        if self.tick_size is not None and self.tick_size <= 0:
            raise ValueError("tick_size must be greater than zero when provided.")

        if self.min_size_ticks is not None and self.min_size_ticks < 1:
            raise ValueError("min_size_ticks must be at least 1 when provided.")

        if self.min_size_ticks is not None and self.tick_size is None:
            raise ValueError("tick_size is required when min_size_ticks is provided.")


@dataclass(frozen=True, slots=True)
class FairValueGap:
    kind: FairValueGapKind
    first_candle_index: int
    middle_candle_index: int
    third_candle_index: int
    detected_at_index: int
    lower: float
    upper: float

    @property
    def size(self) -> float:
        return self.upper - self.lower

    @property
    def equilibrium(self) -> float:
        return (self.lower + self.upper) / 2


def find_fair_value_gaps(
    candles: Sequence[Candle],
    settings: FairValueGapSettings | None = None,
) -> list[FairValueGap]:
    fvg_settings = settings or FairValueGapSettings()
    if len(candles) < 3:
        return []

    gaps: list[FairValueGap] = []

    for third_candle_index in range(2, len(candles)):
        first_candle_index = third_candle_index - 2
        middle_candle_index = third_candle_index - 1
        first_candle = candles[first_candle_index]
        third_candle = candles[third_candle_index]

        bullish_gap = _build_bullish_fvg(
            first_candle=first_candle,
            first_candle_index=first_candle_index,
            middle_candle_index=middle_candle_index,
            third_candle=third_candle,
            third_candle_index=third_candle_index,
        )
        if bullish_gap is not None and _passes_size_filters(bullish_gap, fvg_settings):
            gaps.append(bullish_gap)

        bearish_gap = _build_bearish_fvg(
            first_candle=first_candle,
            first_candle_index=first_candle_index,
            middle_candle_index=middle_candle_index,
            third_candle=third_candle,
            third_candle_index=third_candle_index,
        )
        if bearish_gap is not None and _passes_size_filters(bearish_gap, fvg_settings):
            gaps.append(bearish_gap)

    return gaps


def _build_bullish_fvg(
    *,
    first_candle: Candle,
    first_candle_index: int,
    middle_candle_index: int,
    third_candle: Candle,
    third_candle_index: int,
) -> FairValueGap | None:
    if first_candle.high >= third_candle.low:
        return None

    return FairValueGap(
        kind=FairValueGapKind.BULLISH_FVG,
        first_candle_index=first_candle_index,
        middle_candle_index=middle_candle_index,
        third_candle_index=third_candle_index,
        detected_at_index=third_candle_index,
        lower=first_candle.high,
        upper=third_candle.low,
    )


def _build_bearish_fvg(
    *,
    first_candle: Candle,
    first_candle_index: int,
    middle_candle_index: int,
    third_candle: Candle,
    third_candle_index: int,
) -> FairValueGap | None:
    if first_candle.low <= third_candle.high:
        return None

    return FairValueGap(
        kind=FairValueGapKind.BEARISH_FVG,
        first_candle_index=first_candle_index,
        middle_candle_index=middle_candle_index,
        third_candle_index=third_candle_index,
        detected_at_index=third_candle_index,
        lower=third_candle.high,
        upper=first_candle.low,
    )


def _passes_size_filters(gap: FairValueGap, settings: FairValueGapSettings) -> bool:
    if gap.size < settings.min_absolute_size:
        return False

    if settings.tick_size is None or settings.min_size_ticks is None:
        return True

    return gap.size >= settings.tick_size * settings.min_size_ticks

