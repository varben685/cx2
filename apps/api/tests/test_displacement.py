from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.displacement import (
    CandleDirection,
    DisplacementSettings,
    assess_displacement,
    calculate_prior_atr,
    calculate_prior_volume_ratio,
    candle_direction,
    count_consecutive_directional_candles,
)


def make_candle(
    index: int,
    *,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float | None = None,
) -> Candle:
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )


def test_candle_direction_classifies_bullish_bearish_and_doji() -> None:
    assert candle_direction(make_candle(0, open_price=100, high=103, low=99, close=102)) == (
        CandleDirection.BULLISH
    )
    assert candle_direction(make_candle(1, open_price=102, high=103, low=99, close=100)) == (
        CandleDirection.BEARISH
    )
    assert candle_direction(make_candle(2, open_price=100, high=103, low=99, close=100)) == (
        CandleDirection.DOJI
    )


def test_calculates_prior_atr_without_using_current_candle() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=100, close=101),
        make_candle(1, open_price=101, high=103, low=101, close=102),
        make_candle(2, open_price=102, high=104, low=102, close=103),
        make_candle(3, open_price=103, high=110, low=102, close=109),
    ]

    assert calculate_prior_atr(candles, candle_index=3, period=3) == 2.0


def test_assesses_strong_bullish_displacement_with_volume_confirmation() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=100, close=101, volume=100),
        make_candle(1, open_price=101, high=103, low=101, close=102, volume=100),
        make_candle(2, open_price=102, high=104, low=102, close=103, volume=100),
        make_candle(3, open_price=103, high=111, low=102, close=110, volume=200),
    ]

    assessment = assess_displacement(candles, 3)

    assert assessment.direction == CandleDirection.BULLISH
    assert assessment.atr == 2.0
    assert assessment.body_size == 7.0
    assert assessment.range_size == 9.0
    assert assessment.body_atr_ratio == 3.5
    assert assessment.range_atr_ratio == 4.5
    assert assessment.body_to_range_ratio == pytest.approx(7 / 9)
    assert assessment.consecutive_directional_candles == 4
    assert assessment.volume_ratio == 2.0
    assert assessment.score == 1.0


def test_missing_volume_is_ignored_and_score_is_normalized_over_available_components() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=100, close=101),
        make_candle(1, open_price=101, high=103, low=101, close=102),
        make_candle(2, open_price=102, high=104, low=102, close=103),
        make_candle(3, open_price=103, high=111, low=102, close=110),
    ]

    assessment = assess_displacement(candles, 3)

    assert assessment.volume_ratio is None
    assert assessment.score == 1.0


def test_counts_consecutive_bearish_candles_ending_at_target() -> None:
    candles = [
        make_candle(0, open_price=100, high=101, low=98, close=99),
        make_candle(1, open_price=99, high=100, low=97, close=98),
        make_candle(2, open_price=98, high=99, low=96, close=97),
    ]

    assert count_consecutive_directional_candles(candles, 2) == 3


def test_doji_has_no_consecutive_directional_count() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=99, close=101),
        make_candle(1, open_price=101, high=102, low=100, close=101),
    ]

    assert count_consecutive_directional_candles(candles, 1) == 0


def test_insufficient_prior_data_still_scores_non_atr_components() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=99, close=101),
        make_candle(1, open_price=101, high=106, low=100, close=105),
    ]

    assessment = assess_displacement(candles, 1, DisplacementSettings(atr_period=3))

    assert assessment.atr is None
    assert assessment.body_atr_ratio is None
    assert assessment.range_atr_ratio is None
    assert assessment.body_to_range_ratio == pytest.approx(4 / 6)
    assert assessment.score > 0


def test_volume_ratio_requires_complete_prior_volume_data() -> None:
    candles = [
        make_candle(0, open_price=100, high=102, low=100, close=101, volume=100),
        make_candle(1, open_price=101, high=103, low=101, close=102, volume=None),
        make_candle(2, open_price=102, high=104, low=102, close=103, volume=100),
        make_candle(3, open_price=103, high=110, low=102, close=109, volume=200),
    ]

    assert calculate_prior_volume_ratio(candles, candle_index=3, period=3) is None


def test_rejects_invalid_displacement_settings() -> None:
    with pytest.raises(ValueError, match="atr_period"):
        DisplacementSettings(atr_period=0)

    with pytest.raises(ValueError, match="body_atr_threshold"):
        DisplacementSettings(body_atr_threshold=0)

    with pytest.raises(ValueError, match="volume_weight"):
        DisplacementSettings(volume_weight=-0.1)

    with pytest.raises(ValueError, match="At least one"):
        DisplacementSettings(
            body_atr_weight=0,
            range_atr_weight=0,
            body_to_range_weight=0,
            consecutive_weight=0,
            volume_weight=0,
        )


def test_rejects_out_of_range_candle_index() -> None:
    candles = [make_candle(0, open_price=100, high=102, low=99, close=101)]

    with pytest.raises(IndexError, match="candle_index"):
        assess_displacement(candles, 1)

