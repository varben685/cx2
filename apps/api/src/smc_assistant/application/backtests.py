import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol
from uuid import UUID

from smc_assistant.application.market_data import MarketDataProvider
from smc_assistant.application.outcome_records import (
    OutcomeRecord,
    evaluate_tradingview_record,
)
from smc_assistant.contracts.backtests import BacktestRequest
from smc_assistant.domain.outcomes import OutcomeConfig


class BacktestConflictError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BacktestRun:
    run_id: UUID
    request_sha256: str
    started_at: datetime
    completed_at: datetime
    request: BacktestRequest
    outcomes: tuple[OutcomeRecord, ...]

    def __post_init__(self) -> None:
        if self.run_id != self.request.run_id or any(
            record.run_id != self.run_id for record in self.outcomes
        ):
            raise ValueError("Backtest run IDs must match.")
        if tuple(record.evaluation.event_id for record in self.outcomes) != tuple(
            setup.event_id for setup in self.request.setups
        ):
            raise ValueError("Backtest outcomes must match every requested setup in order.")
        if len({record.outcome_id for record in self.outcomes}) != len(self.outcomes):
            raise ValueError("Backtest outcome IDs must be unique.")


@dataclass(frozen=True, slots=True)
class BacktestSaveResult:
    run: BacktestRun
    created: bool


class BacktestRepository(Protocol):
    def get(self, run_id: UUID) -> BacktestRun | None:
        pass

    def list_recent(self, *, limit: int = 50) -> list[BacktestRun]:
        pass

    def save_completed(self, run: BacktestRun) -> BacktestSaveResult:
        pass


def existing_backtest_result(run: BacktestRun, request_sha256: str) -> BacktestSaveResult:
    if run.request_sha256 != request_sha256:
        raise BacktestConflictError("runId already exists with different input. Use a new runId.")
    return BacktestSaveResult(run=run, created=False)


def execute_backtest(
    request: BacktestRequest,
    provider: MarketDataProvider,
    repository: BacktestRepository,
) -> BacktestSaveResult:
    digest = sha256(
        json.dumps(
            request.model_dump(mode="json", by_alias=True),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    existing = repository.get(request.run_id)
    if existing is not None:
        return existing_backtest_result(existing, digest)

    started_at = datetime.now(UTC)
    config = OutcomeConfig(**request.config.model_dump())
    records = tuple(
        evaluate_tradingview_record(payload, provider, run_id=request.run_id, config=config)
        for payload in request.setups
    )
    return repository.save_completed(
        BacktestRun(
            run_id=request.run_id,
            request_sha256=digest,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            request=request,
            outcomes=records,
        )
    )
