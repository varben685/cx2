from threading import Lock
from uuid import UUID

from smc_assistant.application.backtests import (
    BacktestConflictError,
    BacktestRun,
    BacktestSaveResult,
    existing_backtest_result,
)
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository


class InMemoryBacktestRepository:
    def __init__(self, outcomes: InMemoryOutcomeRepository) -> None:
        self._outcomes = outcomes
        self._runs: dict[UUID, BacktestRun] = {}
        self._lock = Lock()

    def get(self, run_id: UUID) -> BacktestRun | None:
        with self._lock:
            return self._runs.get(run_id)

    def list_recent(self, *, limit: int = 50) -> list[BacktestRun]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        with self._lock:
            return sorted(
                self._runs.values(), key=lambda run: (run.completed_at, run.run_id), reverse=True
            )[:limit]

    def save_completed(self, run: BacktestRun) -> BacktestSaveResult:
        with self._lock:
            existing = self._runs.get(run.run_id)
            if existing is not None:
                return existing_backtest_result(existing, run.request_sha256)
            try:
                self._outcomes.save_new_run(run.run_id, run.outcomes)
            except ValueError as error:
                raise BacktestConflictError(str(error)) from error
            self._runs[run.run_id] = run
            return BacktestSaveResult(run=run, created=True)
