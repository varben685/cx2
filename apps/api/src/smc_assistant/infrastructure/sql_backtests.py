from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.backtests import (
    BacktestConflictError,
    BacktestRun,
    BacktestSaveResult,
    existing_backtest_result,
)
from smc_assistant.infrastructure.sql_outcomes import outcome_record_values
from smc_assistant.infrastructure.webhook_event_schema import backtest_runs, outcome_records

_run_adapter = TypeAdapter(BacktestRun)


class SQLBacktestRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self, run_id: UUID) -> BacktestRun | None:
        with self._engine.connect() as connection:
            snapshot = connection.execute(
                select(backtest_runs.c.snapshot).where(backtest_runs.c.run_id == run_id)
            ).scalar_one_or_none()
        return _run_adapter.validate_python(snapshot) if snapshot is not None else None

    def list_recent(self, *, limit: int = 50) -> list[BacktestRun]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        with self._engine.connect() as connection:
            snapshots = (
                connection.execute(
                    select(backtest_runs.c.snapshot)
                    .order_by(backtest_runs.c.completed_at.desc(), backtest_runs.c.run_id.desc())
                    .limit(limit)
                )
                .scalars()
                .all()
            )
        return [_run_adapter.validate_python(snapshot) for snapshot in snapshots]

    def save_completed(self, run: BacktestRun) -> BacktestSaveResult:
        existing = self.get(run.run_id)
        if existing is not None:
            return existing_backtest_result(existing, run.request_sha256)
        try:
            with self._engine.begin() as connection:
                if (
                    connection.execute(
                        select(outcome_records.c.outcome_id)
                        .where(outcome_records.c.run_id == run.run_id)
                        .limit(1)
                    ).first()
                    is not None
                ):
                    raise BacktestConflictError("runId already has outcome records.")
                connection.execute(
                    insert(backtest_runs).values(
                        run_id=run.run_id,
                        completed_at=run.completed_at,
                        snapshot=_run_adapter.dump_python(run, mode="json"),
                    )
                )
                connection.execute(
                    insert(outcome_records),
                    [outcome_record_values(record) for record in run.outcomes],
                )
        except (IntegrityError, BacktestConflictError):
            existing = self.get(run.run_id)
            if existing is None:
                raise
            return existing_backtest_result(existing, run.request_sha256)
        return BacktestSaveResult(run=run, created=True)
