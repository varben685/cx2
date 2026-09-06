from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from smc_assistant.application.backtest_analytics import summarize_backtest_run
from smc_assistant.application.outcome_records import OutcomeRepository
from smc_assistant.domain.enums import TradeOutcomeLabel

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class BacktestStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

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


class BacktestRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

    run_id: UUID
    symbol: str | None
    statistics: BacktestStatisticsResponse


def get_outcome_repository(request: Request) -> OutcomeRepository:
    return cast(OutcomeRepository, request.app.state.outcome_repository)


@router.get("/summary", response_model=BacktestRunSummaryResponse, response_model_by_alias=True)
def get_backtest_summary(
    repository: Annotated[OutcomeRepository, Depends(get_outcome_repository)],
    run_id: Annotated[UUID, Query(alias="runId")],
    symbol: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
) -> BacktestRunSummaryResponse:
    summary = summarize_backtest_run(repository, run_id, symbol=symbol)
    return BacktestRunSummaryResponse.model_validate(summary)
