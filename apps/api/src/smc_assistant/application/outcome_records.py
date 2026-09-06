from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from smc_assistant.application.market_data import MarketDataProvider
from smc_assistant.application.outcome_evaluation import (
    TradingViewOutcomeEvaluation,
    evaluate_tradingview_outcome,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.enums import TradeOutcomeLabel
from smc_assistant.domain.outcomes import OutcomeConfig

OUTCOME_ENGINE_VERSION = "triple-barrier-v1"


class IncompleteOutcomeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class OutcomeRecord:
    outcome_id: UUID
    run_id: UUID
    schema_version: str
    strategy_version: str
    engine_version: str
    exchange: str
    bar_close_time: datetime
    evaluated_at: datetime
    evaluation: TradingViewOutcomeEvaluation

    def __post_init__(self) -> None:
        for value in (self.bar_close_time, self.evaluated_at):
            if value.utcoffset() is None:
                raise ValueError("Outcome record timestamps must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class OutcomeSaveResult:
    record: OutcomeRecord
    created: bool


class OutcomeRepository(Protocol):
    def save_if_absent(self, record: OutcomeRecord) -> OutcomeSaveResult:
        pass

    def get_by_outcome_id(self, outcome_id: UUID) -> OutcomeRecord | None:
        pass

    def get_by_run_event(self, run_id: UUID, event_id: str) -> OutcomeRecord | None:
        pass

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_id: UUID | None = None,
        event_id: str | None = None,
        symbol: str | None = None,
    ) -> list[OutcomeRecord]:
        pass

    def list_for_run(self, run_id: UUID, *, symbol: str | None = None) -> list[OutcomeRecord]:
        pass


def evaluate_and_save_tradingview_outcome(
    payload: TradingViewWebhookPayload,
    market_data_provider: MarketDataProvider,
    repository: OutcomeRepository,
    *,
    run_id: UUID,
    config: OutcomeConfig | None = None,
) -> OutcomeSaveResult:
    existing = repository.get_by_run_event(run_id, payload.event_id)
    if existing is not None:
        return OutcomeSaveResult(record=existing, created=False)

    return repository.save_if_absent(
        evaluate_tradingview_record(payload, market_data_provider, run_id=run_id, config=config)
    )


def evaluate_tradingview_record(
    payload: TradingViewWebhookPayload,
    market_data_provider: MarketDataProvider,
    *,
    run_id: UUID,
    config: OutcomeConfig | None = None,
) -> OutcomeRecord:
    evaluation = evaluate_tradingview_outcome(payload, market_data_provider, config)
    outcome = evaluation.outcome
    if (
        outcome.label == TradeOutcomeLabel.NOT_TRIGGERED
        and evaluation.candles_loaded < evaluation.config.entry_timeout_bars
    ) or (
        outcome.label == TradeOutcomeLabel.TIMEOUT
        and (outcome.bars_held or 0) < evaluation.config.max_holding_bars
    ):
        raise IncompleteOutcomeError("Not enough candles to persist a final outcome.")
    return OutcomeRecord(
        outcome_id=uuid4(),
        run_id=run_id,
        schema_version=payload.schema_version,
        strategy_version=payload.strategy_version,
        engine_version=OUTCOME_ENGINE_VERSION,
        exchange=payload.exchange,
        bar_close_time=payload.bar_close_time.astimezone(UTC),
        evaluated_at=datetime.now(UTC),
        evaluation=evaluation,
    )
