from csv import Error as CsvError
from datetime import datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from smc_assistant.analytics.backtest import summarize_outcomes
from smc_assistant.api.analytics import BacktestStatisticsResponse
from smc_assistant.api.outcomes import CamelResponse
from smc_assistant.application.backtests import (
    BacktestConflictError,
    BacktestRepository,
    BacktestRun,
    execute_backtest,
)
from smc_assistant.contracts.backtests import BacktestConfig, BacktestRequest
from smc_assistant.infrastructure.csv_market_data import CsvMarketDataProvider

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


class BacktestResponse(CamelResponse):
    run_id: UUID
    status: Literal["COMPLETED"] = "COMPLETED"
    started_at: datetime
    completed_at: datetime
    symbol: str
    exchange: str
    timeframe: str
    strategy_version: str
    request_sha256: str
    config: BacktestConfig
    outcome_ids: list[UUID]
    statistics: BacktestStatisticsResponse


class BacktestListResponse(CamelResponse):
    count: int
    items: list[BacktestResponse]


def get_backtest_repository(request: Request) -> BacktestRepository:
    return cast(BacktestRepository, request.app.state.backtest_repository)


def backtest_response(run: BacktestRun) -> BacktestResponse:
    first = run.request.setups[0]
    return BacktestResponse(
        run_id=run.run_id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        symbol=first.symbol,
        exchange=first.exchange,
        timeframe=first.timeframe,
        strategy_version=first.strategy_version,
        request_sha256=run.request_sha256,
        config=run.request.config,
        outcome_ids=[record.outcome_id for record in run.outcomes],
        statistics=BacktestStatisticsResponse.model_validate(
            summarize_outcomes(record.evaluation.outcome for record in run.outcomes)
        ),
    )


@router.post("", response_model=BacktestResponse, status_code=201)
def create_backtest(
    payload: BacktestRequest,
    response: Response,
    repository: Annotated[BacktestRepository, Depends(get_backtest_repository)],
) -> BacktestResponse:
    try:
        result = execute_backtest(
            payload, CsvMarketDataProvider(csv_text=payload.candles_csv), repository
        )
    except BacktestConflictError as error:
        raise HTTPException(409, str(error)) from error
    except CsvError as error:
        raise HTTPException(422, "CSV parsing failed.") from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    if not result.created:
        response.status_code = 200
    return backtest_response(result.run)


@router.get("", response_model=BacktestListResponse)
def list_backtests(
    repository: Annotated[BacktestRepository, Depends(get_backtest_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> BacktestListResponse:
    runs = repository.list_recent(limit=limit)
    return BacktestListResponse(count=len(runs), items=[backtest_response(run) for run in runs])


@router.get("/{run_id}", response_model=BacktestResponse)
def get_backtest(
    run_id: UUID,
    repository: Annotated[BacktestRepository, Depends(get_backtest_repository)],
) -> BacktestResponse:
    run = repository.get(run_id)
    if run is None:
        raise HTTPException(404, "Backtest not found.")
    return backtest_response(run)
