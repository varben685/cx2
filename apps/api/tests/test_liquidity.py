from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.liquidity import (
    LiquiditySweep,
    LiquiditySweepKind,
    LiquiditySweepSettings,
    find_liquidity_sweeps,
)
from smc_assistant.domain.market_structure import ConfirmedPivot, PivotKind


def make_candle(
    index: int,
    *,
    high: float,
    low: float,
    close: float | None = None,
) -> Candle:
    midpoint = (high + low) / 2
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=midpoint,
        high=high,
        low=low,
        close=close if close is not None else midpoint,
        volume=None,
    )


def make_pivot(
    kind: PivotKind,
    *,
    candle_index: int = 2,
    confirmed_at_index: int = 4,
    price: float,
) -> ConfirmedPivot:
    return ConfirmedPivot(
        kind=kind,
        candle_index=candle_index,
        confirmed_at_index=confirmed_at_index,
        price=price,
    )


def test_finds_bullish_sweep_when_swing_low_is_wicked_and_reclaimed_same_candle() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=101.0, low=88.0, close=92.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(candles, [pivot])

    assert sweeps == [
        LiquiditySweep(
            kind=LiquiditySweepKind.BULLISH_SWEEP,
            sweep_candle_index=5,
            confirmed_at_index=5,
            swept_pivot=pivot,
            swept_level=90.0,
            wick_extreme=88.0,
            confirmation_close=92.0,
        )
    ]


def test_finds_bearish_sweep_when_swing_high_is_wicked_and_rejected_same_candle() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0, close=108.0),
    ]
    pivot = make_pivot(PivotKind.SWING_HIGH, price=110.0)

    sweeps = find_liquidity_sweeps(candles, [pivot])

    assert sweeps == [
        LiquiditySweep(
            kind=LiquiditySweepKind.BEARISH_SWEEP,
            sweep_candle_index=5,
            confirmed_at_index=5,
            swept_pivot=pivot,
            swept_level=110.0,
            wick_extreme=112.0,
            confirmation_close=108.0,
        )
    ]


def test_supports_later_confirmation_inside_configured_window() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=95.0, low=88.0, close=89.0),
        make_candle(6, high=97.0, low=90.5, close=91.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(
        candles,
        [pivot],
        LiquiditySweepSettings(max_confirmation_bars=1),
    )

    assert len(sweeps) == 1
    assert sweeps[0].sweep_candle_index == 5
    assert sweeps[0].confirmed_at_index == 6
    assert sweeps[0].confirmation_close == 91.0


def test_ignores_later_confirmation_outside_configured_window() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=95.0, low=88.0, close=89.0),
        make_candle(6, high=97.0, low=90.5, close=91.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(candles, [pivot])

    assert sweeps == []


def test_requires_pivot_to_be_known_before_sweep_candle() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=101.0, low=88.0, close=92.0),
    ]
    pivot_confirmed_on_sweep_candle = make_pivot(
        PivotKind.SWING_LOW,
        confirmed_at_index=4,
        price=90.0,
    )

    sweeps = find_liquidity_sweeps(candles, [pivot_confirmed_on_sweep_candle])

    assert sweeps == []


def test_requires_wick_to_cross_level_not_only_touch_it() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=101.0, low=90.0, close=92.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(candles, [pivot])

    assert sweeps == []


def test_sweep_buffer_requires_extra_wick_distance_beyond_level() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=101.0, low=89.5, close=92.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(
        candles,
        [pivot],
        LiquiditySweepSettings(sweep_buffer=1.0),
    )

    assert sweeps == []


def test_sweep_is_emitted_once_per_pivot() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=101.0, low=88.0, close=92.0),
        make_candle(6, high=100.0, low=87.0, close=93.0),
    ]
    pivot = make_pivot(PivotKind.SWING_LOW, price=90.0)

    sweeps = find_liquidity_sweeps(candles, [pivot])

    assert len(sweeps) == 1
    assert sweeps[0].sweep_candle_index == 5


def test_rejects_invalid_liquidity_sweep_settings() -> None:
    with pytest.raises(ValueError, match="sweep_buffer"):
        LiquiditySweepSettings(sweep_buffer=-0.01)

    with pytest.raises(ValueError, match="max_confirmation_bars"):
        LiquiditySweepSettings(max_confirmation_bars=-1)
