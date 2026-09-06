from collections.abc import Iterable
from dataclasses import dataclass
from math import fsum, isfinite

from smc_assistant.domain.enums import TradeOutcomeLabel
from smc_assistant.domain.outcomes import TradeOutcome

_CLOSED_LABELS = frozenset(
    {
        TradeOutcomeLabel.WIN,
        TradeOutcomeLabel.LOSS,
        TradeOutcomeLabel.BREAK_EVEN,
        TradeOutcomeLabel.TIMEOUT,
    }
)


@dataclass(frozen=True, slots=True)
class BacktestStatistics:
    total_setups: int
    closed_trades: int
    excluded_setups: int
    outcome_counts: dict[TradeOutcomeLabel, int]
    net_wins: int
    net_losses: int
    net_break_even: int
    net_win_rate: float | None
    total_net_r: float
    net_expectancy_r: float | None
    net_profit_r: float
    net_loss_r: float
    net_profit_factor: float | None


def summarize_outcomes(outcomes: Iterable[TradeOutcome]) -> BacktestStatistics:
    counts = dict.fromkeys(TradeOutcomeLabel, 0)
    returns: list[float] = []
    for outcome in outcomes:
        counts[outcome.label] += 1
        if outcome.label not in _CLOSED_LABELS:
            continue
        net_r = outcome.net_realized_r
        if net_r is None or not isfinite(net_r):
            raise ValueError("Closed trade outcomes must have finite net_realized_r.")
        returns.append(net_r)

    closed_trades = len(returns)
    total_setups = sum(counts.values())
    total_net_r = fsum(returns)
    net_profit_r = fsum(value for value in returns if value > 0)
    net_loss_r = fsum(-value for value in returns if value < 0)
    net_wins = sum(value > 0 for value in returns)
    net_losses = sum(value < 0 for value in returns)

    return BacktestStatistics(
        total_setups=total_setups,
        closed_trades=closed_trades,
        excluded_setups=total_setups - closed_trades,
        outcome_counts=counts,
        net_wins=net_wins,
        net_losses=net_losses,
        net_break_even=closed_trades - net_wins - net_losses,
        net_win_rate=round(net_wins / closed_trades, 6) if closed_trades else None,
        total_net_r=round(total_net_r, 4),
        net_expectancy_r=round(total_net_r / closed_trades, 6) if closed_trades else None,
        net_profit_r=round(net_profit_r, 4),
        net_loss_r=round(net_loss_r, 4),
        net_profit_factor=round(net_profit_r / net_loss_r, 6) if net_loss_r else None,
    )
