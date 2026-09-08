from datetime import datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from smc_assistant.application.backtest_analytics import summarize_backtest_run
from smc_assistant.application.backtests import BacktestRepository
from smc_assistant.application.journal import JournalRepository
from smc_assistant.application.outcome_records import OutcomeRepository
from smc_assistant.application.performance_analytics import (
    BacktestPerformanceReport,
    ComponentScoreState,
    build_performance_report,
)
from smc_assistant.domain.enums import TradeOutcomeLabel
from smc_assistant.domain.setup_scoring import ScoreComponentName

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


class RiskStatisticsResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    average_win_r: float | None
    average_loss_r: float | None
    maximum_drawdown_r: float
    longest_winning_streak: int
    longest_losing_streak: int


class EquityPointResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    sequence: int
    event_id: str
    occurred_at: datetime
    net_r: float
    cumulative_net_r: float
    drawdown_r: float


class AnalyticsBreakdownResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    key: str
    label: str
    statistics: BacktestStatisticsResponse


class AnalyticsBreakdownListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    run_id: UUID
    count: int
    items: list[AnalyticsBreakdownResponse]


class ComponentBreakdownResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    component: ScoreComponentName
    state: ComponentScoreState
    statistics: BacktestStatisticsResponse


class DecisionComparisonResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    journaled_setups: int
    taken: int
    skipped: int
    not_recorded: int
    followed_recommendation: int
    overrode_recommendation: int
    manual_overrides: int
    agreement_rate: float | None
    taken_statistics: BacktestStatisticsResponse
    skipped_statistics: BacktestStatisticsResponse


class BacktestPerformanceReportResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )

    run_id: UUID
    scoring_config_version: str
    statistics: BacktestStatisticsResponse
    risk: RiskStatisticsResponse
    equity_curve: list[EquityPointResponse]
    by_session: list[AnalyticsBreakdownResponse]
    by_instrument: list[AnalyticsBreakdownResponse]
    by_direction: list[AnalyticsBreakdownResponse]
    by_score_bucket: list[AnalyticsBreakdownResponse]
    by_strategy_version: list[AnalyticsBreakdownResponse]
    by_setup_component: list[ComponentBreakdownResponse]
    decisions: DecisionComparisonResponse


def get_outcome_repository(request: Request) -> OutcomeRepository:
    return cast(OutcomeRepository, request.app.state.outcome_repository)


def get_backtest_repository(request: Request) -> BacktestRepository:
    return cast(BacktestRepository, request.app.state.backtest_repository)


def get_journal_repository(request: Request) -> JournalRepository:
    return cast(JournalRepository, request.app.state.journal_repository)


@router.get("/summary", response_model=BacktestRunSummaryResponse, response_model_by_alias=True)
def get_backtest_summary(
    repository: Annotated[OutcomeRepository, Depends(get_outcome_repository)],
    run_id: Annotated[UUID, Query(alias="runId")],
    symbol: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
) -> BacktestRunSummaryResponse:
    summary = summarize_backtest_run(repository, run_id, symbol=symbol)
    return BacktestRunSummaryResponse.model_validate(summary)


@router.get(
    "/report",
    response_model=BacktestPerformanceReportResponse,
    response_model_by_alias=True,
)
def get_performance_report(
    run_id: Annotated[UUID, Query(alias="runId")],
    backtest_repository: Annotated[
        BacktestRepository,
        Depends(get_backtest_repository),
    ],
    journal_repository: Annotated[
        JournalRepository,
        Depends(get_journal_repository),
    ],
) -> BacktestPerformanceReportResponse:
    report = _load_performance_report(
        run_id,
        backtest_repository=backtest_repository,
        journal_repository=journal_repository,
    )
    return BacktestPerformanceReportResponse.model_validate(report)


@router.get(
    "/by-session",
    response_model=AnalyticsBreakdownListResponse,
    response_model_by_alias=True,
)
def get_session_breakdown(
    run_id: Annotated[UUID, Query(alias="runId")],
    backtest_repository: Annotated[
        BacktestRepository,
        Depends(get_backtest_repository),
    ],
    journal_repository: Annotated[
        JournalRepository,
        Depends(get_journal_repository),
    ],
) -> AnalyticsBreakdownListResponse:
    report = _load_performance_report(
        run_id,
        backtest_repository=backtest_repository,
        journal_repository=journal_repository,
    )
    return AnalyticsBreakdownListResponse(
        run_id=run_id,
        count=len(report.by_session),
        items=[
            AnalyticsBreakdownResponse.model_validate(item)
            for item in report.by_session
        ],
    )


@router.get(
    "/by-score-bucket",
    response_model=AnalyticsBreakdownListResponse,
    response_model_by_alias=True,
)
def get_score_bucket_breakdown(
    run_id: Annotated[UUID, Query(alias="runId")],
    backtest_repository: Annotated[
        BacktestRepository,
        Depends(get_backtest_repository),
    ],
    journal_repository: Annotated[
        JournalRepository,
        Depends(get_journal_repository),
    ],
) -> AnalyticsBreakdownListResponse:
    report = _load_performance_report(
        run_id,
        backtest_repository=backtest_repository,
        journal_repository=journal_repository,
    )
    return AnalyticsBreakdownListResponse(
        run_id=run_id,
        count=len(report.by_score_bucket),
        items=[
            AnalyticsBreakdownResponse.model_validate(item)
            for item in report.by_score_bucket
        ],
    )


def _load_performance_report(
    run_id: UUID,
    *,
    backtest_repository: BacktestRepository,
    journal_repository: JournalRepository,
) -> BacktestPerformanceReport:
    run = backtest_repository.get(run_id)
    if run is None:
        raise HTTPException(404, "Backtest not found.")
    return build_performance_report(run, journal_repository)
