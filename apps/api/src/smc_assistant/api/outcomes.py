from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from smc_assistant.api.analytics import get_outcome_repository
from smc_assistant.application.outcome_records import OutcomeRecord, OutcomeRepository
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.outcomes import OutcomeExitReason

router = APIRouter(prefix="/api/v1/outcomes", tags=["outcomes"])


class CamelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)


class CostResponse(CamelResponse):
    commission_amount: float
    slippage_amount: float
    total_amount: float
    cost_r: float


class ExcursionResponse(CamelResponse):
    mfe_r: float
    mae_r: float
    max_favorable_price: float
    max_adverse_price: float


class TradeOutcomeResponse(CamelResponse):
    label: TradeOutcomeLabel
    exit_reason: OutcomeExitReason
    realized_r: float | None
    net_realized_r: float | None
    costs: CostResponse | None
    excursion: ExcursionResponse | None
    entry_time: datetime | None
    exit_time: datetime | None
    exit_price: float | None
    bars_to_entry: int | None
    bars_held: int | None


class OutcomeResponse(CamelResponse):
    outcome_id: UUID
    run_id: UUID
    event_id: str
    symbol: str
    timeframe: str
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float
    evaluated_at: datetime
    engine_version: str
    market_data_sha256: str
    outcome: TradeOutcomeResponse


class OutcomeListResponse(CamelResponse):
    count: int
    items: list[OutcomeResponse]


def outcome_response(record: OutcomeRecord) -> OutcomeResponse:
    evaluation = record.evaluation
    return OutcomeResponse(
        outcome_id=record.outcome_id,
        run_id=record.run_id,
        event_id=evaluation.event_id,
        symbol=evaluation.symbol,
        timeframe=evaluation.timeframe,
        direction=evaluation.trade_plan.direction,
        entry_price=evaluation.trade_plan.entry_price,
        stop_loss=evaluation.trade_plan.stop_loss,
        take_profit=evaluation.trade_plan.take_profit,
        evaluated_at=record.evaluated_at,
        engine_version=record.engine_version,
        market_data_sha256=evaluation.market_data_sha256,
        outcome=TradeOutcomeResponse.model_validate(evaluation.outcome),
    )


@router.get("", response_model=OutcomeListResponse)
def list_outcomes(
    repository: Annotated[OutcomeRepository, Depends(get_outcome_repository)],
    run_id: Annotated[UUID, Query(alias="runId")],
    symbol: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> OutcomeListResponse:
    records = repository.list_recent(run_id=run_id, symbol=symbol, limit=limit)
    return OutcomeListResponse(count=len(records), items=[outcome_response(r) for r in records])


@router.get("/{outcome_id}", response_model=OutcomeResponse)
def get_outcome(
    outcome_id: UUID,
    repository: Annotated[OutcomeRepository, Depends(get_outcome_repository)],
) -> OutcomeResponse:
    record = repository.get_by_outcome_id(outcome_id)
    if record is None:
        raise HTTPException(404, "Outcome not found.")
    return outcome_response(record)
