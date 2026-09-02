from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.market_structure import (
    CharacterChange,
    CharacterChangeKind,
    ConfirmedPivot,
    MarketBias,
    PivotKind,
    PivotSettings,
    StructureBreak,
    StructureBreakKind,
    StructureBreakSettings,
    find_bos_events,
    find_choch_events,
    find_confirmed_pivots,
)


def make_candle(
    index: int,
    *,
    high: float,
    low: float,
    open_price: float | None = None,
    close: float | None = None,
) -> Candle:
    midpoint = (high + low) / 2
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=open_price if open_price is not None else midpoint,
        high=high,
        low=low,
        close=close if close is not None else midpoint,
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


def test_finds_bullish_bos_when_known_swing_high_is_broken_by_close() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0, close=111.0),
    ]
    pivots = find_confirmed_pivots(candles[:5], PivotSettings(left_bars=2, right_bars=2))

    events = find_bos_events(candles, pivots)

    assert events == [
        StructureBreak(
            kind=StructureBreakKind.BULLISH_BOS,
            candle_index=5,
            broken_pivot=ConfirmedPivot(
                kind=PivotKind.SWING_HIGH,
                candle_index=2,
                confirmed_at_index=4,
                price=110.0,
            ),
            broken_level=110.0,
            break_price=111.0,
        )
    ]


def test_finds_bearish_bos_when_known_swing_low_is_broken_by_close() -> None:
    candles = [
        make_candle(0, high=110.0, low=100.0),
        make_candle(1, high=108.0, low=98.0),
        make_candle(2, high=106.0, low=90.0),
        make_candle(3, high=109.0, low=96.0),
        make_candle(4, high=112.0, low=99.0),
        make_candle(5, high=98.0, low=84.0, close=89.0),
    ]
    pivots = find_confirmed_pivots(candles[:5], PivotSettings(left_bars=2, right_bars=2))

    events = find_bos_events(candles, pivots)

    assert events == [
        StructureBreak(
            kind=StructureBreakKind.BEARISH_BOS,
            candle_index=5,
            broken_pivot=ConfirmedPivot(
                kind=PivotKind.SWING_LOW,
                candle_index=2,
                confirmed_at_index=4,
                price=90.0,
            ),
            broken_level=90.0,
            break_price=89.0,
        )
    ]


def test_close_confirmation_ignores_wick_only_break() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0),
    ]
    pivot = ConfirmedPivot(
        kind=PivotKind.SWING_HIGH,
        candle_index=2,
        confirmed_at_index=4,
        price=110.0,
    )

    events = find_bos_events(candles, [pivot], StructureBreakSettings(close_confirmation=True))

    assert events == []


def test_can_detect_wick_break_when_close_confirmation_is_disabled() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0, close=111.0),
    ]
    pivot = ConfirmedPivot(
        kind=PivotKind.SWING_HIGH,
        candle_index=2,
        confirmed_at_index=4,
        price=110.0,
    )

    events = find_bos_events(candles, [pivot], StructureBreakSettings(close_confirmation=False))

    assert events[0].kind == StructureBreakKind.BULLISH_BOS
    assert events[0].break_price == 112.0


def test_break_buffer_requires_extra_distance_beyond_pivot_level() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0),
    ]
    pivot = ConfirmedPivot(
        kind=PivotKind.SWING_HIGH,
        candle_index=2,
        confirmed_at_index=4,
        price=110.0,
    )

    events = find_bos_events(candles, [pivot], StructureBreakSettings(break_buffer=1.0))

    assert events == []


def test_bos_requires_pivot_to_be_known_before_break_candle() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=112.0, low=100.0, close=111.0),
    ]
    pivot_confirmed_on_break_candle = ConfirmedPivot(
        kind=PivotKind.SWING_HIGH,
        candle_index=2,
        confirmed_at_index=4,
        price=110.0,
    )

    events = find_bos_events(candles, [pivot_confirmed_on_break_candle])

    assert events == []


def test_bos_is_emitted_once_per_broken_pivot() -> None:
    candles = [
        make_candle(0, high=100.0, low=90.0),
        make_candle(1, high=103.0, low=92.0),
        make_candle(2, high=110.0, low=95.0),
        make_candle(3, high=104.0, low=93.0),
        make_candle(4, high=101.0, low=91.0),
        make_candle(5, high=112.0, low=100.0, close=111.0),
        make_candle(6, high=114.0, low=102.0, close=113.0),
    ]
    pivot = ConfirmedPivot(
        kind=PivotKind.SWING_HIGH,
        candle_index=2,
        confirmed_at_index=4,
        price=110.0,
    )

    events = find_bos_events(candles, [pivot])

    assert len(events) == 1
    assert events[0].candle_index == 5


def test_rejects_negative_break_buffer() -> None:
    with pytest.raises(ValueError, match="break_buffer"):
        StructureBreakSettings(break_buffer=-0.01)


def make_pivot(
    kind: PivotKind,
    *,
    index: int,
    confirmed_at_index: int,
    price: float,
) -> ConfirmedPivot:
    return ConfirmedPivot(
        kind=kind,
        candle_index=index,
        confirmed_at_index=confirmed_at_index,
        price=price,
    )


def make_structure_break(kind: StructureBreakKind, *, candle_index: int) -> StructureBreak:
    if kind == StructureBreakKind.BULLISH_BOS:
        pivot = make_pivot(
            PivotKind.SWING_HIGH,
            index=candle_index - 3,
            confirmed_at_index=candle_index - 1,
            price=110.0,
        )
        return StructureBreak(
            kind=kind,
            candle_index=candle_index,
            broken_pivot=pivot,
            broken_level=110.0,
            break_price=111.0,
        )

    pivot = make_pivot(
        PivotKind.SWING_LOW,
        index=candle_index - 3,
        confirmed_at_index=candle_index - 1,
        price=90.0,
    )
    return StructureBreak(
        kind=kind,
        candle_index=candle_index,
        broken_pivot=pivot,
        broken_level=90.0,
        break_price=89.0,
    )


def test_finds_bullish_choch_when_bearish_bias_breaks_upward() -> None:
    bullish_break = make_structure_break(StructureBreakKind.BULLISH_BOS, candle_index=8)

    events = find_choch_events([bullish_break], initial_bias=MarketBias.BEARISH)

    assert events == [
        CharacterChange(
            kind=CharacterChangeKind.BULLISH_CHOCH,
            candle_index=8,
            previous_bias=MarketBias.BEARISH,
            new_bias=MarketBias.BULLISH,
            triggering_break=bullish_break,
        )
    ]


def test_finds_bearish_choch_when_bullish_bias_breaks_downward() -> None:
    bearish_break = make_structure_break(StructureBreakKind.BEARISH_BOS, candle_index=8)

    events = find_choch_events([bearish_break], initial_bias=MarketBias.BULLISH)

    assert events == [
        CharacterChange(
            kind=CharacterChangeKind.BEARISH_CHOCH,
            candle_index=8,
            previous_bias=MarketBias.BULLISH,
            new_bias=MarketBias.BEARISH,
            triggering_break=bearish_break,
        )
    ]


def test_same_direction_structure_break_does_not_create_choch() -> None:
    bullish_break = make_structure_break(StructureBreakKind.BULLISH_BOS, candle_index=8)

    assert find_choch_events([bullish_break], initial_bias=MarketBias.BULLISH) == []


def test_neutral_bias_uses_first_break_as_context_without_choch() -> None:
    first_break = make_structure_break(StructureBreakKind.BULLISH_BOS, candle_index=8)
    second_break = make_structure_break(StructureBreakKind.BEARISH_BOS, candle_index=12)

    events = find_choch_events([first_break, second_break])

    assert events == [
        CharacterChange(
            kind=CharacterChangeKind.BEARISH_CHOCH,
            candle_index=12,
            previous_bias=MarketBias.BULLISH,
            new_bias=MarketBias.BEARISH,
            triggering_break=second_break,
        )
    ]


def test_choch_classification_is_chronological_even_if_input_is_unsorted() -> None:
    later_bullish_break = make_structure_break(StructureBreakKind.BULLISH_BOS, candle_index=14)
    earlier_bearish_break = make_structure_break(StructureBreakKind.BEARISH_BOS, candle_index=10)

    events = find_choch_events(
        [later_bullish_break, earlier_bearish_break],
        initial_bias=MarketBias.BULLISH,
    )

    assert events == [
        CharacterChange(
            kind=CharacterChangeKind.BEARISH_CHOCH,
            candle_index=10,
            previous_bias=MarketBias.BULLISH,
            new_bias=MarketBias.BEARISH,
            triggering_break=earlier_bearish_break,
        ),
        CharacterChange(
            kind=CharacterChangeKind.BULLISH_CHOCH,
            candle_index=14,
            previous_bias=MarketBias.BEARISH,
            new_bias=MarketBias.BULLISH,
            triggering_break=later_bullish_break,
        ),
    ]
