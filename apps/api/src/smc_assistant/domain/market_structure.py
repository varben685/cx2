from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.candles import Candle


class PivotKind(StrEnum):
    SWING_HIGH = "SWING_HIGH"
    SWING_LOW = "SWING_LOW"


class StructureBreakKind(StrEnum):
    BULLISH_BOS = "BULLISH_BOS"
    BEARISH_BOS = "BEARISH_BOS"


class MarketBias(StrEnum):
    NEUTRAL = "NEUTRAL"
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"


class CharacterChangeKind(StrEnum):
    BULLISH_CHOCH = "BULLISH_CHOCH"
    BEARISH_CHOCH = "BEARISH_CHOCH"


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


@dataclass(frozen=True, slots=True)
class StructureBreakSettings:
    break_buffer: float = 0.0
    close_confirmation: bool = True

    def __post_init__(self) -> None:
        if self.break_buffer < 0:
            raise ValueError("break_buffer must be non-negative.")


@dataclass(frozen=True, slots=True)
class StructureBreak:
    kind: StructureBreakKind
    candle_index: int
    broken_pivot: ConfirmedPivot
    broken_level: float
    break_price: float


@dataclass(frozen=True, slots=True)
class CharacterChange:
    kind: CharacterChangeKind
    candle_index: int
    previous_bias: MarketBias
    new_bias: MarketBias
    triggering_break: StructureBreak


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


def find_bos_events(
    candles: Sequence[Candle],
    pivots: Sequence[ConfirmedPivot],
    settings: StructureBreakSettings | None = None,
) -> list[StructureBreak]:
    break_settings = settings or StructureBreakSettings()
    events: list[StructureBreak] = []
    already_broken: set[tuple[PivotKind, int, int]] = set()

    for candle_index, candle in enumerate(candles):
        known_pivots = [
            pivot
            for pivot in pivots
            if pivot.confirmed_at_index < candle_index
            and (pivot.kind, pivot.candle_index, pivot.confirmed_at_index) not in already_broken
        ]

        for pivot in known_pivots:
            event = _detect_bos_for_pivot(candle_index, candle, pivot, break_settings)
            if event is None:
                continue

            events.append(event)
            already_broken.add((pivot.kind, pivot.candle_index, pivot.confirmed_at_index))

    return events


def find_choch_events(
    structure_breaks: Sequence[StructureBreak],
    initial_bias: MarketBias = MarketBias.NEUTRAL,
) -> list[CharacterChange]:
    current_bias = initial_bias
    events: list[CharacterChange] = []

    ordered_breaks = sorted(
        enumerate(structure_breaks),
        key=lambda indexed_break: (indexed_break[1].candle_index, indexed_break[0]),
    )

    for _, structure_break in ordered_breaks:
        break_bias = _bias_from_structure_break(structure_break)
        if current_bias == MarketBias.NEUTRAL:
            current_bias = break_bias
            continue

        if break_bias == current_bias:
            continue

        events.append(
            CharacterChange(
                kind=_choch_kind_for_new_bias(break_bias),
                candle_index=structure_break.candle_index,
                previous_bias=current_bias,
                new_bias=break_bias,
                triggering_break=structure_break,
            )
        )
        current_bias = break_bias

    return events


def _detect_bos_for_pivot(
    candle_index: int,
    candle: Candle,
    pivot: ConfirmedPivot,
    settings: StructureBreakSettings,
) -> StructureBreak | None:
    if pivot.kind == PivotKind.SWING_HIGH:
        threshold = pivot.price + settings.break_buffer
        break_price = candle.close if settings.close_confirmation else candle.high
        if break_price > threshold:
            return StructureBreak(
                kind=StructureBreakKind.BULLISH_BOS,
                candle_index=candle_index,
                broken_pivot=pivot,
                broken_level=pivot.price,
                break_price=break_price,
            )

    if pivot.kind == PivotKind.SWING_LOW:
        threshold = pivot.price - settings.break_buffer
        break_price = candle.close if settings.close_confirmation else candle.low
        if break_price < threshold:
            return StructureBreak(
                kind=StructureBreakKind.BEARISH_BOS,
                candle_index=candle_index,
                broken_pivot=pivot,
                broken_level=pivot.price,
                break_price=break_price,
            )

    return None


def _bias_from_structure_break(structure_break: StructureBreak) -> MarketBias:
    if structure_break.kind == StructureBreakKind.BULLISH_BOS:
        return MarketBias.BULLISH

    return MarketBias.BEARISH


def _choch_kind_for_new_bias(new_bias: MarketBias) -> CharacterChangeKind:
    if new_bias == MarketBias.BULLISH:
        return CharacterChangeKind.BULLISH_CHOCH

    return CharacterChangeKind.BEARISH_CHOCH


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
