from dataclasses import replace

import pytest

from smc_assistant.analytics.backtest import summarize_outcomes
from smc_assistant.domain.enums import TradeOutcomeLabel
from smc_assistant.domain.outcomes import OutcomeExitReason, TradeOutcome


def outcome(net_r: float | None, label: TradeOutcomeLabel = TradeOutcomeLabel.WIN):
    return TradeOutcome(
        label=label,
        exit_reason=OutcomeExitReason.TAKE_PROFIT_HIT,
        realized_r=net_r,
        net_realized_r=net_r,
        costs=None,
        excursion=None,
        entry_time=None,
        exit_time=None,
        exit_price=None,
        bars_to_entry=None,
        bars_held=None,
    )


def test_net_statistics_include_timeouts_and_exclude_untraded_setups():
    summary = summarize_outcomes(
        [
            outcome(2),
            outcome(-1, TradeOutcomeLabel.LOSS),
            outcome(0.5, TradeOutcomeLabel.TIMEOUT),
            outcome(-0.5, TradeOutcomeLabel.TIMEOUT),
            outcome(0, TradeOutcomeLabel.BREAK_EVEN),
            outcome(None, TradeOutcomeLabel.NOT_TRIGGERED),
            outcome(None, TradeOutcomeLabel.CANCELLED),
            outcome(None, TradeOutcomeLabel.INVALIDATED),
        ]
    )

    assert summary.total_setups == 8
    assert summary.closed_trades == 5
    assert summary.excluded_setups == 3
    assert summary.net_wins == 2
    assert summary.net_losses == 2
    assert summary.net_break_even == 1
    assert summary.net_win_rate == 0.4
    assert summary.total_net_r == 1
    assert summary.net_expectancy_r == 0.2
    assert summary.net_profit_r == 2.5
    assert summary.net_loss_r == 1.5
    assert summary.net_profit_factor == 1.666667
    assert summary.outcome_counts[TradeOutcomeLabel.TIMEOUT] == 2
    assert summary.outcome_counts[TradeOutcomeLabel.WIN] == 1


def test_net_sign_not_barrier_label_determines_win_rate():
    summary = summarize_outcomes([replace(outcome(-0.1), realized_r=0.05)])

    assert summary.outcome_counts[TradeOutcomeLabel.WIN] == 1
    assert summary.net_wins == 0
    assert summary.net_losses == 1
    assert summary.net_win_rate == 0
    assert summary.net_profit_factor == 0


@pytest.mark.parametrize("outcomes", [[], [outcome(None, TradeOutcomeLabel.NOT_TRIGGERED)]])
def test_no_closed_trades_has_null_rates(outcomes):
    summary = summarize_outcomes(outcomes)
    assert summary.closed_trades == 0
    assert summary.total_net_r == 0
    assert summary.net_win_rate is None
    assert summary.net_expectancy_r is None
    assert summary.net_profit_factor is None
    assert summary.net_profit_r == summary.net_loss_r == 0
    assert set(summary.outcome_counts) == set(TradeOutcomeLabel)


@pytest.mark.parametrize("returns, win_rate", [([1, 2], 1), ([0, 0], 0)])
def test_no_losses_has_undefined_profit_factor(returns, win_rate):
    summary = summarize_outcomes(outcome(value) for value in returns)
    assert summary.net_profit_factor is None
    assert summary.net_loss_r == 0
    assert summary.net_win_rate == win_rate


@pytest.mark.parametrize("invalid", [None, float("nan"), float("inf"), -float("inf")])
def test_rejects_missing_or_non_finite_closed_trade_returns(invalid):
    with pytest.raises(ValueError, match="finite net_realized_r"):
        summarize_outcomes([outcome(invalid, TradeOutcomeLabel.TIMEOUT)])


def test_summation_is_order_independent_and_rounds_only_final_metrics():
    outcomes = [outcome(0.1), outcome(0.2), outcome(-0.3)]
    forward = summarize_outcomes(outcomes)
    backward = summarize_outcomes(reversed(outcomes))
    assert forward == backward
    assert forward.total_net_r == 0
    assert forward.net_expectancy_r == 0
    assert forward.net_profit_factor == 1
