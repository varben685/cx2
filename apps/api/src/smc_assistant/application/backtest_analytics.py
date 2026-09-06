from dataclasses import dataclass
from uuid import UUID

from smc_assistant.analytics.backtest import BacktestStatistics, summarize_outcomes
from smc_assistant.application.outcome_records import OutcomeRepository


@dataclass(frozen=True, slots=True)
class BacktestRunSummary:
    run_id: UUID
    symbol: str | None
    statistics: BacktestStatistics


def summarize_backtest_run(
    repository: OutcomeRepository,
    run_id: UUID,
    *,
    symbol: str | None = None,
) -> BacktestRunSummary:
    records = repository.list_for_run(run_id, symbol=symbol)
    return BacktestRunSummary(
        run_id=run_id,
        symbol=symbol,
        statistics=summarize_outcomes(record.evaluation.outcome for record in records),
    )
