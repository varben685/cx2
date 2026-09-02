from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.candles import Candle


class CandleDirection(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    DOJI = "DOJI"


@dataclass(frozen=True, slots=True)
class DisplacementSettings:
    atr_period: int = 3
    body_atr_threshold: float = 1.0
    range_atr_threshold: float = 1.2
    body_to_range_threshold: float = 0.6
    consecutive_candles_threshold: int = 2
    volume_ratio_threshold: float = 1.5
    body_atr_weight: float = 0.3
    range_atr_weight: float = 0.2
    body_to_range_weight: float = 0.2
    consecutive_weight: float = 0.2
    volume_weight: float = 0.1

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError("atr_period must be at least 1.")

        positive_thresholds = {
            "body_atr_threshold": self.body_atr_threshold,
            "range_atr_threshold": self.range_atr_threshold,
            "body_to_range_threshold": self.body_to_range_threshold,
            "consecutive_candles_threshold": float(self.consecutive_candles_threshold),
            "volume_ratio_threshold": self.volume_ratio_threshold,
        }
        for name, value in positive_thresholds.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")

        weights = {
            "body_atr_weight": self.body_atr_weight,
            "range_atr_weight": self.range_atr_weight,
            "body_to_range_weight": self.body_to_range_weight,
            "consecutive_weight": self.consecutive_weight,
            "volume_weight": self.volume_weight,
        }
        for name, value in weights.items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")

        if sum(weights.values()) <= 0:
            raise ValueError("At least one displacement weight must be greater than zero.")


@dataclass(frozen=True, slots=True)
class DisplacementAssessment:
    candle_index: int
    direction: CandleDirection
    atr: float | None
    body_size: float
    range_size: float
    body_atr_ratio: float | None
    range_atr_ratio: float | None
    body_to_range_ratio: float
    consecutive_directional_candles: int
    volume_ratio: float | None
    score: float


def assess_displacement(
    candles: Sequence[Candle],
    candle_index: int,
    settings: DisplacementSettings | None = None,
) -> DisplacementAssessment:
    displacement_settings = settings or DisplacementSettings()
    if candle_index < 0 or candle_index >= len(candles):
        raise IndexError("candle_index is out of range.")

    candle = candles[candle_index]
    body_size = abs(candle.close - candle.open)
    range_size = candle.high - candle.low
    direction = candle_direction(candle)
    body_to_range_ratio = body_size / range_size if range_size > 0 else 0.0

    atr = calculate_prior_atr(candles, candle_index, displacement_settings.atr_period)
    body_atr_ratio = body_size / atr if atr is not None else None
    range_atr_ratio = range_size / atr if atr is not None else None
    consecutive_directional_candles = count_consecutive_directional_candles(candles, candle_index)
    volume_ratio = calculate_prior_volume_ratio(
        candles,
        candle_index,
        displacement_settings.atr_period,
    )

    score = _weighted_score(
        body_atr_ratio=body_atr_ratio,
        range_atr_ratio=range_atr_ratio,
        body_to_range_ratio=body_to_range_ratio,
        consecutive_directional_candles=consecutive_directional_candles,
        volume_ratio=volume_ratio,
        settings=displacement_settings,
    )

    return DisplacementAssessment(
        candle_index=candle_index,
        direction=direction,
        atr=atr,
        body_size=body_size,
        range_size=range_size,
        body_atr_ratio=body_atr_ratio,
        range_atr_ratio=range_atr_ratio,
        body_to_range_ratio=body_to_range_ratio,
        consecutive_directional_candles=consecutive_directional_candles,
        volume_ratio=volume_ratio,
        score=score,
    )


def candle_direction(candle: Candle) -> CandleDirection:
    if candle.close > candle.open:
        return CandleDirection.BULLISH

    if candle.close < candle.open:
        return CandleDirection.BEARISH

    return CandleDirection.DOJI


def calculate_prior_atr(candles: Sequence[Candle], candle_index: int, period: int) -> float | None:
    if period < 1:
        raise ValueError("period must be at least 1.")

    if candle_index < period:
        return None

    start_index = candle_index - period
    true_ranges = [_true_range(candles, index) for index in range(start_index, candle_index)]
    return sum(true_ranges) / period


def count_consecutive_directional_candles(candles: Sequence[Candle], candle_index: int) -> int:
    direction = candle_direction(candles[candle_index])
    if direction == CandleDirection.DOJI:
        return 0

    count = 0
    for index in range(candle_index, -1, -1):
        if candle_direction(candles[index]) != direction:
            break

        count += 1

    return count


def calculate_prior_volume_ratio(
    candles: Sequence[Candle],
    candle_index: int,
    period: int,
) -> float | None:
    if period < 1:
        raise ValueError("period must be at least 1.")

    if candle_index < period:
        return None

    current_volume = candles[candle_index].volume
    prior_volumes = [candle.volume for candle in candles[candle_index - period : candle_index]]
    if current_volume is None or any(volume is None for volume in prior_volumes):
        return None

    average_prior_volume = sum(volume for volume in prior_volumes if volume is not None) / period
    if average_prior_volume <= 0:
        return None

    return current_volume / average_prior_volume


def _true_range(candles: Sequence[Candle], index: int) -> float:
    candle = candles[index]
    if index == 0:
        return candle.high - candle.low

    previous_close = candles[index - 1].close
    return max(
        candle.high - candle.low,
        abs(candle.high - previous_close),
        abs(candle.low - previous_close),
    )


def _weighted_score(
    *,
    body_atr_ratio: float | None,
    range_atr_ratio: float | None,
    body_to_range_ratio: float,
    consecutive_directional_candles: int,
    volume_ratio: float | None,
    settings: DisplacementSettings,
) -> float:
    weighted_components: list[tuple[float, float]] = [
        (
            _score_optional_ratio(body_atr_ratio, settings.body_atr_threshold),
            settings.body_atr_weight if body_atr_ratio is not None else 0.0,
        ),
        (
            _score_optional_ratio(range_atr_ratio, settings.range_atr_threshold),
            settings.range_atr_weight if range_atr_ratio is not None else 0.0,
        ),
        (
            _score_ratio(body_to_range_ratio, settings.body_to_range_threshold),
            settings.body_to_range_weight,
        ),
        (
            _score_ratio(
                float(consecutive_directional_candles),
                float(settings.consecutive_candles_threshold),
            ),
            settings.consecutive_weight,
        ),
        (
            _score_optional_ratio(volume_ratio, settings.volume_ratio_threshold),
            settings.volume_weight if volume_ratio is not None else 0.0,
        ),
    ]
    active_weight = sum(weight for _, weight in weighted_components)
    if active_weight <= 0:
        return 0.0

    weighted_sum = sum(component_score * weight for component_score, weight in weighted_components)
    return weighted_sum / active_weight


def _score_optional_ratio(value: float | None, threshold: float) -> float:
    if value is None:
        return 0.0

    return _score_ratio(value, threshold)


def _score_ratio(value: float, threshold: float) -> float:
    return max(0.0, min(value / threshold, 1.0))

