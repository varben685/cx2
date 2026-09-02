from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.fair_value_gaps import (
    FairValueGap,
    FairValueGapKind,
    FairValueGapSettings,
    find_fair_value_gaps,
)


def make_candle(index: int, *, high: float, low: float) -> Candle:
    midpoint = (high + low) / 2
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=midpoint,
        high=high,
        low=low,
        close=midpoint,
        volume=None,
    )


def test_finds_bullish_three_candle_fair_value_gap() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=107.0, low=98.0),
        make_candle(2, high=112.0, low=104.0),
    ]

    gaps = find_fair_value_gaps(candles)

    assert gaps == [
        FairValueGap(
            kind=FairValueGapKind.BULLISH_FVG,
            first_candle_index=0,
            middle_candle_index=1,
            third_candle_index=2,
            detected_at_index=2,
            lower=100.0,
            upper=104.0,
        )
    ]
    assert gaps[0].size == 4.0
    assert gaps[0].equilibrium == 102.0


def test_finds_bearish_three_candle_fair_value_gap() -> None:
    candles = [
        make_candle(0, high=110.0, low=104.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=100.0, low=94.0),
    ]

    gaps = find_fair_value_gaps(candles)

    assert gaps == [
        FairValueGap(
            kind=FairValueGapKind.BEARISH_FVG,
            first_candle_index=0,
            middle_candle_index=1,
            third_candle_index=2,
            detected_at_index=2,
            lower=100.0,
            upper=104.0,
        )
    ]
    assert gaps[0].size == 4.0
    assert gaps[0].equilibrium == 102.0


def test_does_not_emit_gap_when_first_and_third_candle_touch() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=104.0, low=98.0),
        make_candle(2, high=108.0, low=100.0),
    ]

    assert find_fair_value_gaps(candles) == []


def test_does_not_emit_gap_with_fewer_than_three_candles() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=104.0, low=98.0),
    ]

    assert find_fair_value_gaps(candles) == []


def test_filters_gap_below_min_absolute_size() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=105.0, low=99.0),
        make_candle(2, high=108.0, low=101.0),
    ]

    gaps = find_fair_value_gaps(candles, FairValueGapSettings(min_absolute_size=2.0))

    assert gaps == []


def test_filters_gap_below_min_tick_size() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=105.0, low=99.0),
        make_candle(2, high=108.0, low=101.0),
    ]

    gaps = find_fair_value_gaps(
        candles,
        FairValueGapSettings(tick_size=0.25, min_size_ticks=5),
    )

    assert gaps == []


def test_accepts_gap_at_minimum_tick_size_threshold() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=105.0, low=99.0),
        make_candle(2, high=108.0, low=101.25),
    ]

    gaps = find_fair_value_gaps(
        candles,
        FairValueGapSettings(tick_size=0.25, min_size_ticks=5),
    )

    assert len(gaps) == 1
    assert gaps[0].size == 1.25


def test_scans_overlapping_three_candle_windows() -> None:
    candles = [
        make_candle(0, high=100.0, low=95.0),
        make_candle(1, high=106.0, low=99.0),
        make_candle(2, high=112.0, low=104.0),
        make_candle(3, high=109.0, low=101.0),
        make_candle(4, high=98.0, low=90.0),
    ]

    gaps = find_fair_value_gaps(candles)

    assert [gap.kind for gap in gaps] == [
        FairValueGapKind.BULLISH_FVG,
        FairValueGapKind.BEARISH_FVG,
    ]
    assert [(gap.first_candle_index, gap.third_candle_index) for gap in gaps] == [(0, 2), (2, 4)]


def test_rejects_invalid_fvg_settings() -> None:
    with pytest.raises(ValueError, match="min_absolute_size"):
        FairValueGapSettings(min_absolute_size=-0.01)

    with pytest.raises(ValueError, match="tick_size"):
        FairValueGapSettings(tick_size=0)

    with pytest.raises(ValueError, match="min_size_ticks"):
        FairValueGapSettings(tick_size=0.25, min_size_ticks=0)

    with pytest.raises(ValueError, match="tick_size"):
        FairValueGapSettings(min_size_ticks=2)

