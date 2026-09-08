from dataclasses import dataclass
from datetime import datetime
from math import fsum, isfinite

from smc_assistant.application.outcome_records import OutcomeRecord
from smc_assistant.domain.enums import TradeOutcomeLabel

_CLOSED_LABELS = frozenset(
    {
        TradeOutcomeLabel.WIN,
        TradeOutcomeLabel.LOSS,
        TradeOutcomeLabel.BREAK_EVEN,
        TradeOutcomeLabel.TIMEOUT,
    }
)


@dataclass(frozen=True, slots=True)
class EquityPoint:
    sequence: int
    event_id: str
    occurred_at: datetime
    net_r: float
    cumulative_net_r: float
    drawdown_r: float


@dataclass(frozen=True, slots=True)
class RiskStatistics:
    average_win_r: float | None
    average_loss_r: float | None
    maximum_drawdown_r: float
    longest_winning_streak: int
    longest_losing_streak: int


@dataclass(frozen=True, slots=True)
class PerformanceAnalysis:
    risk: RiskStatistics
    equity_curve: tuple[EquityPoint, ...]


def analyze_performance(records: list[OutcomeRecord]) -> PerformanceAnalysis:
    closed_records = sorted(
        (
            record
            for record in records
            if record.evaluation.outcome.label in _CLOSED_LABELS
        ),
        key=lambda record: (
            record.evaluation.outcome.exit_time or record.bar_close_time,
            record.outcome_id,
        ),
    )
    returns: list[float] = []
    points: list[EquityPoint] = []
    cumulative = 0.0
    peak = 0.0
    maximum_drawdown = 0.0
    winning_streak = 0
    losing_streak = 0
    longest_winning_streak = 0
    longest_losing_streak = 0

    for sequence, record in enumerate(closed_records, start=1):
        outcome = record.evaluation.outcome
        net_r = outcome.net_realized_r
        if net_r is None or not isfinite(net_r):
            raise ValueError("Closed trade outcomes must have finite net_realized_r.")
        returns.append(net_r)
        cumulative = fsum((cumulative, net_r))
        peak = max(peak, cumulative)
        drawdown = peak - cumulative
        maximum_drawdown = max(maximum_drawdown, drawdown)

        if net_r > 0:
            winning_streak += 1
            losing_streak = 0
        elif net_r < 0:
            losing_streak += 1
            winning_streak = 0
        else:
            winning_streak = 0
            losing_streak = 0
        longest_winning_streak = max(longest_winning_streak, winning_streak)
        longest_losing_streak = max(longest_losing_streak, losing_streak)
        points.append(
            EquityPoint(
                sequence=sequence,
                event_id=record.evaluation.event_id,
                occurred_at=outcome.exit_time or record.bar_close_time,
                net_r=net_r,
                cumulative_net_r=round(cumulative, 4),
                drawdown_r=round(drawdown, 4),
            )
        )

    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value < 0]
    return PerformanceAnalysis(
        risk=RiskStatistics(
            average_win_r=round(fsum(wins) / len(wins), 6) if wins else None,
            average_loss_r=round(fsum(losses) / len(losses), 6) if losses else None,
            maximum_drawdown_r=round(maximum_drawdown, 4),
            longest_winning_streak=longest_winning_streak,
            longest_losing_streak=longest_losing_streak,
        ),
        equity_curve=tuple(points),
    )
