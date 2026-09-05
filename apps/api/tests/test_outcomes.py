from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.outcomes import (
    OutcomeConfig,
    OutcomeExitReason,
    TradePlan,
    evaluate_triple_barrier_outcome,
)


def make_candle(
    index: int,
    *,
    open_price: float = 100.0,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.0,
) -> Candle:
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1000.0,
    )


def test_long_outcome_wins_when_take_profit_is_hit_after_entry() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        ),
        [
            make_candle(0, high=101.0, low=99.0),
            make_candle(1, high=111.0, low=100.0),
        ],
    )

    assert outcome.label == TradeOutcomeLabel.WIN
    assert outcome.exit_reason == OutcomeExitReason.TAKE_PROFIT_HIT
    assert outcome.realized_r == 2.0
    assert outcome.exit_price == 110.0
    assert outcome.net_realized_r == 2.0
    assert outcome.costs is not None
    assert outcome.costs.total_amount == 0.0
    assert outcome.costs.cost_r == 0.0
    assert outcome.bars_to_entry == 1
    assert outcome.bars_held == 2


def test_short_outcome_loses_when_stop_loss_is_hit_after_entry() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.SHORT,
            entry_price=100.0,
            stop_loss=105.0,
            take_profit=90.0,
        ),
        [
            make_candle(0, high=101.0, low=99.0),
            make_candle(1, high=106.0, low=95.0),
        ],
    )

    assert outcome.label == TradeOutcomeLabel.LOSS
    assert outcome.exit_reason == OutcomeExitReason.STOP_LOSS_HIT
    assert outcome.realized_r == -1.0
    assert outcome.net_realized_r == -1.0
    assert outcome.exit_price == 105.0


def test_outcome_uses_stop_first_when_both_barriers_are_hit_in_same_candle() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        ),
        [make_candle(0, high=112.0, low=94.0)],
    )

    assert outcome.label == TradeOutcomeLabel.LOSS
    assert outcome.exit_reason == OutcomeExitReason.STOP_LOSS_HIT
    assert outcome.realized_r == -1.0


def test_outcome_times_out_at_vertical_barrier_close() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        ),
        [
            make_candle(0, high=101.0, low=99.0, close=101.0),
            make_candle(1, high=104.0, low=100.0, close=103.0),
        ],
        OutcomeConfig(max_holding_bars=2, entry_timeout_bars=1),
    )

    assert outcome.label == TradeOutcomeLabel.TIMEOUT
    assert outcome.exit_reason == OutcomeExitReason.VERTICAL_BARRIER_HIT
    assert outcome.exit_price == 103.0
    assert outcome.realized_r == 0.6
    assert outcome.bars_held == 2


def test_outcome_is_not_triggered_when_entry_is_not_touched_before_timeout() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        ),
        [
            make_candle(0, open_price=98.0, high=99.0, low=96.0, close=98.0),
            make_candle(1, open_price=98.5, high=99.5, low=96.0, close=99.0),
        ],
        OutcomeConfig(max_holding_bars=5, entry_timeout_bars=2),
    )

    assert outcome.label == TradeOutcomeLabel.NOT_TRIGGERED
    assert outcome.exit_reason == OutcomeExitReason.ENTRY_NOT_TRIGGERED
    assert outcome.realized_r is None
    assert outcome.entry_time is None
    assert outcome.exit_time is None
    assert outcome.net_realized_r is None
    assert outcome.costs is None


def test_trade_plan_validates_directional_price_order() -> None:
    with pytest.raises(ValueError, match="Long trade requires"):
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=105.0,
            take_profit=110.0,
        )

    with pytest.raises(ValueError, match="Short trade requires"):
        TradePlan(
            direction=TradeDirection.SHORT,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=90.0,
        )


def test_outcome_rejects_non_chronological_future_candles() -> None:
    with pytest.raises(ValueError, match="sorted by open_time"):
        evaluate_triple_barrier_outcome(
            TradePlan(
                direction=TradeDirection.LONG,
                entry_price=100.0,
                stop_loss=95.0,
                take_profit=110.0,
            ),
            [make_candle(1), make_candle(0)],
        )


def test_outcome_applies_commission_and_slippage_costs_to_net_r() -> None:
    outcome = evaluate_triple_barrier_outcome(
        TradePlan(
            direction=TradeDirection.LONG,
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
        ),
        [
            make_candle(0, high=101.0, low=99.0),
            make_candle(1, high=111.0, low=100.0),
        ],
        OutcomeConfig(
            max_holding_bars=5,
            entry_timeout_bars=2,
            commission_bps_per_side=10.0,
            slippage_bps_per_side=5.0,
        ),
    )

    assert outcome.realized_r == 2.0
    assert outcome.net_realized_r == 1.937
    assert outcome.costs is not None
    assert outcome.costs.commission_amount == 0.21
    assert outcome.costs.slippage_amount == 0.105
    assert outcome.costs.total_amount == 0.315
    assert outcome.costs.cost_r == 0.063


def test_outcome_config_rejects_negative_costs() -> None:
    with pytest.raises(ValueError, match="commission_bps_per_side"):
        OutcomeConfig(commission_bps_per_side=-0.01)

    with pytest.raises(ValueError, match="slippage_bps_per_side"):
        OutcomeConfig(slippage_bps_per_side=-0.01)
