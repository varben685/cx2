from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.market_structure import (
    ConfirmedPivot,
    PivotKind,
    PivotSettings,
    find_confirmed_pivots,
)


def make_candle(index: int, *, high: float, low: float) -> Candle:
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=(high + low) / 2,
        high=high,
        low=low,
        close=(high + low) / 2,
        volume=None,
    )


def test_finds_confirmed_swing_high_after_right_bars_close() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
    ]

    pivots = find_confirmed_pivots(candles, PivotSettings(left_bars=2, right_bars=2))

    assert pivots == [
        ConfirmedPivot(
            kind=PivotKind.SWING_HIGH,
            candle_index=2,
            confirmed_at_index=4,
            price=110.0,
        )
    ]
    assert pivots[0].recognition_lag_bars == 2


def test_does_not_emit_pivot_before_required_right_bars_exist() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
    ]

    assert find_confirmed_pivots(candles, PivotSettings(left_bars=2, right_bars=2)) == []


def test_finds_confirmed_swing_low_after_right_bars_close() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
    ]

    pivots = find_confirmed_pivots(candles, PivotSettings(left_bars=2, right_bars=2))

    assert pivots == [
        ConfirmedPivot(
            kind=PivotKind.SWING_LOW,
            candle_index=2,
            confirmed_at_index=4,
            price=90.0,
        )
    ]


def test_equal_neighbor_high_does_not_create_strict_swing_high() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=110.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
    ]

    assert find_confirmed_pivots(candles, PivotSettings(left_bars=2, right_bars=2)) == []


def test_rejects_invalid_pivot_settings() -> None:
    with pytest.raises(ValueError, match="left_bars"):
        PivotSettings(left_bars=0, right_bars=2)
