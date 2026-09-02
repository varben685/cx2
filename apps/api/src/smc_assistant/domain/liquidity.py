from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.market_structure import ConfirmedPivot, PivotKind


class LiquiditySweepKind(StrEnum):
    BULLISH_SWEEP = "BULLISH_SWEEP"
    BEARISH_SWEEP = "BEARISH_SWEEP"


@dataclass(frozen=True, slots=True)
class LiquiditySweepSettings:
    sweep_buffer: float = 0.0
    max_confirmation_bars: int = 0

    def __post_init__(self) -> None:
        if self.sweep_buffer < 0:
            raise ValueError("sweep_buffer must be non-negative.")

        if self.max_confirmation_bars < 0:
            raise ValueError("max_confirmation_bars must be non-negative.")


@dataclass(frozen=True, slots=True)
class LiquiditySweep:
    kind: LiquiditySweepKind
    sweep_candle_index: int
    confirmed_at_index: int
    swept_pivot: ConfirmedPivot
    swept_level: float
    wick_extreme: float
    confirmation_close: float


def find_liquidity_sweeps(
    candles: Sequence[Candle],
    pivots: Sequence[ConfirmedPivot],
    settings: LiquiditySweepSettings | None = None,
) -> list[LiquiditySweep]:
    sweep_settings = settings or LiquiditySweepSettings()
    events: list[LiquiditySweep] = []
    swept_pivots: set[tuple[PivotKind, int, int]] = set()

    for candle_index, candle in enumerate(candles):
        known_pivots = [
            pivot
            for pivot in pivots
            if pivot.confirmed_at_index < candle_index
            and (pivot.kind, pivot.candle_index, pivot.confirmed_at_index) not in swept_pivots
        ]

        for pivot in known_pivots:
            sweep = _find_sweep_for_pivot(
                candles=candles,
                sweep_candle_index=candle_index,
                sweep_candle=candle,
                pivot=pivot,
                settings=sweep_settings,
            )
            if sweep is None:
                continue

            events.append(sweep)
            swept_pivots.add((pivot.kind, pivot.candle_index, pivot.confirmed_at_index))

    return events


def _find_sweep_for_pivot(
    *,
    candles: Sequence[Candle],
    sweep_candle_index: int,
    sweep_candle: Candle,
    pivot: ConfirmedPivot,
    settings: LiquiditySweepSettings,
) -> LiquiditySweep | None:
    if pivot.kind == PivotKind.SWING_LOW:
        return _find_bullish_sweep(
            candles=candles,
            sweep_candle_index=sweep_candle_index,
            sweep_candle=sweep_candle,
            pivot=pivot,
            settings=settings,
        )

    return _find_bearish_sweep(
        candles=candles,
        sweep_candle_index=sweep_candle_index,
        sweep_candle=sweep_candle,
        pivot=pivot,
        settings=settings,
    )


def _find_bullish_sweep(
    *,
    candles: Sequence[Candle],
    sweep_candle_index: int,
    sweep_candle: Candle,
    pivot: ConfirmedPivot,
    settings: LiquiditySweepSettings,
) -> LiquiditySweep | None:
    sweep_threshold = pivot.price - settings.sweep_buffer
    if sweep_candle.low >= sweep_threshold:
        return None

    for confirmation_index in _confirmation_range(candles, sweep_candle_index, settings):
        confirmation_candle = candles[confirmation_index]
        if confirmation_candle.close > pivot.price:
            return LiquiditySweep(
                kind=LiquiditySweepKind.BULLISH_SWEEP,
                sweep_candle_index=sweep_candle_index,
                confirmed_at_index=confirmation_index,
                swept_pivot=pivot,
                swept_level=pivot.price,
                wick_extreme=sweep_candle.low,
                confirmation_close=confirmation_candle.close,
            )

    return None


def _find_bearish_sweep(
    *,
    candles: Sequence[Candle],
    sweep_candle_index: int,
    sweep_candle: Candle,
    pivot: ConfirmedPivot,
    settings: LiquiditySweepSettings,
) -> LiquiditySweep | None:
    sweep_threshold = pivot.price + settings.sweep_buffer
    if sweep_candle.high <= sweep_threshold:
        return None

    for confirmation_index in _confirmation_range(candles, sweep_candle_index, settings):
        confirmation_candle = candles[confirmation_index]
        if confirmation_candle.close < pivot.price:
            return LiquiditySweep(
                kind=LiquiditySweepKind.BEARISH_SWEEP,
                sweep_candle_index=sweep_candle_index,
                confirmed_at_index=confirmation_index,
                swept_pivot=pivot,
                swept_level=pivot.price,
                wick_extreme=sweep_candle.high,
                confirmation_close=confirmation_candle.close,
            )

    return None


def _confirmation_range(
    candles: Sequence[Candle],
    sweep_candle_index: int,
    settings: LiquiditySweepSettings,
) -> range:
    last_confirmation_index = min(
        len(candles) - 1,
        sweep_candle_index + settings.max_confirmation_bars,
    )
    return range(sweep_candle_index, last_confirmation_index + 1)

