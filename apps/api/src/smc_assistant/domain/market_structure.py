from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.candles import Candle


class PivotKind(StrEnum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


@dataclass(frozen=True, slots=True)
class ConfirmedPivot:
    kind: PivotKind
    candle_index: int
    confirmed_at_index: int
    price: float

    @property
    def recognition_lag_bars(self) -> int:
        return self.confirmed_at_index - self.candle_index


@dataclass(frozen=True, slots=True)
class PivotSettings:
    left_bars: int = 2
    right_bars: int = 2

    def __post_init__(self) -> None:
        if self.left_bars < 1:
            raise ValueError("left_bars must be at least 1.")

        if self.right_bars < 1:
            raise ValueError("right_bars must be at least 1.")


def find_confirmed_pivots(
    candles: Sequence[Candle],
    settings: PivotSettings | None = None,
) -> list[ConfirmedPivot]:
    pivot_settings = settings or PivotSettings()
    if len(candles) < pivot_settings.left_bars + pivot_settings.right_bars + 1:
        return []

    pivots: list[ConfirmedPivot] = []
    first_candidate = pivot_settings.left_bars
    last_candidate = len(candles) - pivot_settings.right_bars - 1

    for candidate_index in range(first_candidate, last_candidate + 1):
        candidate = candles[candidate_index]
        left_window = candles[candidate_index - pivot_settings.left_bars : candidate_index]
        right_window_end = candidate_index + pivot_settings.right_bars + 1
        right_window = candles[candidate_index + 1 : right_window_end]

        if _is_strict_swing_high(candidate, left_window, right_window):
            pivots.append(
                ConfirmedPivot(
                    kind=PivotKind.SWING_HIGH,
                    candle_index=candidate_index,
                    confirmed_at_index=candidate_index + pivot_settings.right_bars,
                    price=candidate.high,
                )
            )

        if _is_strict_swing_low(candidate, left_window, right_window):
            pivots.append(
                ConfirmedPivot(
                    kind=PivotKind.SWING_LOW,
                    candle_index=candidate_index,
                    confirmed_at_index=candidate_index + pivot_settings.right_bars,
                    price=candidate.low,
                )
            )

    return pivots


def _is_strict_swing_high(
    candidate: Candle,
    left_window: Sequence[Candle],
    right_window: Sequence[Candle],
) -> bool:
    surrounding_highs = [candle.high for candle in [*left_window, *right_window]]
    return all(candidate.high > high for high in surrounding_highs)


def _is_strict_swing_low(
    candidate: Candle,
    left_window: Sequence[Candle],
    right_window: Sequence[Candle],
) -> bool:
    surrounding_lows = [candle.low for candle in [*left_window, *right_window]]
    return all(candidate.low < low for low in surrounding_lows)
