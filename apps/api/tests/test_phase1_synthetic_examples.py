from smc_assistant.domain.displacement import CandleDirection, assess_displacement
from smc_assistant.domain.fair_value_gaps import FairValueGapKind, find_fair_value_gaps
from smc_assistant.domain.liquidity import LiquiditySweepKind, find_liquidity_sweeps
from smc_assistant.domain.market_structure import (
    CharacterChangeKind,
    PivotKind,
    PivotSettings,
    StructureBreakKind,
    find_bos_events,
    find_choch_events,
    find_confirmed_pivots,
)
from smc_assistant.domain.synthetic_examples import build_phase1_synthetic_candles


def test_phase1_synthetic_candles_contain_core_domain_events() -> None:
    candles = build_phase1_synthetic_candles()

    pivots = find_confirmed_pivots(candles, PivotSettings(left_bars=1, right_bars=1))
    bos_events = find_bos_events(candles, pivots)
    choch_events = find_choch_events(bos_events)
    fair_value_gaps = find_fair_value_gaps(candles)
    liquidity_sweeps = find_liquidity_sweeps(candles, pivots)
    displacement = assess_displacement(candles, candle_index=5)

    assert any(
        pivot.kind == PivotKind.SWING_LOW
        and pivot.candle_index == 2
        and pivot.confirmed_at_index == 3
        and pivot.price == 94.0
        for pivot in pivots
    )
    assert any(
        pivot.kind == PivotKind.SWING_HIGH
        and pivot.candle_index == 3
        and pivot.confirmed_at_index == 4
        and pivot.price == 107.0
        for pivot in pivots
    )

    assert any(
        event.kind == StructureBreakKind.BEARISH_BOS
        and event.candle_index == 4
        and event.broken_level == 94.0
        for event in bos_events
    )
    assert any(
        event.kind == StructureBreakKind.BULLISH_BOS
        and event.candle_index == 5
        and event.broken_level == 107.0
        for event in bos_events
    )

    assert any(
        event.kind == CharacterChangeKind.BULLISH_CHOCH
        and event.candle_index == 5
        for event in choch_events
    )

    assert any(
        gap.kind == FairValueGapKind.BULLISH_FVG
        and gap.first_candle_index == 3
        and gap.third_candle_index == 5
        and gap.lower == 107.0
        and gap.upper == 108.0
        for gap in fair_value_gaps
    )
    assert any(
        gap.kind == FairValueGapKind.BEARISH_FVG
        and gap.first_candle_index == 5
        and gap.third_candle_index == 7
        and gap.lower == 105.0
        and gap.upper == 108.0
        for gap in fair_value_gaps
    )

    assert any(
        sweep.kind == LiquiditySweepKind.BULLISH_SWEEP
        and sweep.sweep_candle_index == 6
        and sweep.swept_level == 94.0
        for sweep in liquidity_sweeps
    )

    assert displacement.direction == CandleDirection.BULLISH
    assert displacement.candle_index == 5
    assert displacement.atr is not None
    assert displacement.score > 0.7

