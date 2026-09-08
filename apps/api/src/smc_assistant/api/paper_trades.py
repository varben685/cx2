from collections.abc import Callable
from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.application.paper_trading import (
    PaperTradeAlreadyExistsError,
    PaperTradeNotFoundError,
    PaperTradeRepository,
    PaperTradeRevisionConflictError,
    PaperTradeRiskRejectedError,
    PaperTradeSetupNotFoundError,
    PaperTradeTransitionError,
    PaperTradingService,
)
from smc_assistant.contracts.paper_trading import (
    PaperTradeCancelRequest,
    PaperTradeCloseRequest,
    PaperTradeCreateRequest,
    PaperTradePriceRequest,
)
from smc_assistant.domain.paper_trading import PaperTrade, PaperTradeEvent, PaperTradeStatus

router = APIRouter(prefix="/api/v1/paper-trades", tags=["paper-trading"])


class CamelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class RiskDecisionResponse(CamelResponse):
    approved: bool
    policy_version: str = Field(alias="policyVersion")
    rejection_reasons: list[str] = Field(alias="rejectionReasons")
    daily_loss_r: float = Field(alias="dailyLossR")
    consecutive_losses: int = Field(alias="consecutiveLosses")
    open_positions: int = Field(alias="openPositions")


class PaperTradeResponse(CamelResponse):
    trade_id: UUID = Field(alias="tradeId")
    setup_id: str = Field(alias="setupId")
    event_id: str = Field(alias="eventId")
    symbol: str
    exchange: str
    timeframe: str
    direction: str
    session: str
    strategy_version: str = Field(alias="strategyVersion")
    status: PaperTradeStatus
    entry_price: float = Field(alias="entryPrice")
    stop_loss: float = Field(alias="stopLoss")
    take_profit: float = Field(alias="takeProfit")
    planned_risk_reward: float = Field(alias="plannedRiskReward")
    account_balance: float = Field(alias="accountBalance")
    risk_percent: float = Field(alias="riskPercent")
    risk_amount: float = Field(alias="riskAmount")
    quantity: float
    opened_at: datetime | None = Field(alias="openedAt")
    closed_at: datetime | None = Field(alias="closedAt")
    exit_price: float | None = Field(alias="exitPrice")
    exit_reason: str | None = Field(alias="exitReason")
    realized_pnl: float | None = Field(alias="realizedPnl")
    realized_r: float | None = Field(alias="realizedR")
    risk_policy_version: str = Field(alias="riskPolicyVersion")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    revision: int


class PaperTradeCreationResponse(PaperTradeResponse):
    risk_decision: RiskDecisionResponse = Field(alias="riskDecision")


class PaperTradeListResponse(CamelResponse):
    count: int
    items: list[PaperTradeResponse]


class PaperTradeEventResponse(CamelResponse):
    trade_id: UUID = Field(alias="tradeId")
    sequence: int
    event_type: str = Field(alias="eventType")
    occurred_at: datetime = Field(alias="occurredAt")
    details: dict[str, Any]


class PaperTradeEventListResponse(CamelResponse):
    count: int
    items: list[PaperTradeEventResponse]


def get_paper_trading_service(request: Request) -> PaperTradingService:
    return cast(PaperTradingService, request.app.state.paper_trading_service)


def get_paper_trade_repository(request: Request) -> PaperTradeRepository:
    return cast(PaperTradeRepository, request.app.state.paper_trade_repository)


@router.post(
    "",
    response_model=PaperTradeCreationResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_paper_trade(
    payload: PaperTradeCreateRequest,
    service: Annotated[PaperTradingService, Depends(get_paper_trading_service)],
) -> PaperTradeCreationResponse:
    try:
        creation = service.create_trade(
            payload.setup_id,
            account_balance=payload.account_balance,
            risk_percent=payload.risk_percent,
        )
    except PaperTradeSetupNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except PaperTradeAlreadyExistsError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except PaperTradeRiskRejectedError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    return PaperTradeCreationResponse.model_validate(
        {
            **_trade_data(creation.trade),
            "riskDecision": {
                "approved": creation.risk_decision.approved,
                "policyVersion": creation.risk_decision.policy_version,
                "rejectionReasons": list(creation.risk_decision.rejection_reasons),
                "dailyLossR": creation.risk_decision.daily_loss_r,
                "consecutiveLosses": creation.risk_decision.consecutive_losses,
                "openPositions": creation.risk_decision.open_positions,
            },
        }
    )


@router.get("", response_model=PaperTradeListResponse, response_model_by_alias=True)
def list_paper_trades(
    repository: Annotated[PaperTradeRepository, Depends(get_paper_trade_repository)],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    trade_status: Annotated[PaperTradeStatus | None, Query(alias="status")] = None,
    symbol: str | None = None,
) -> PaperTradeListResponse:
    trades = repository.list_recent(limit=limit, status=trade_status, symbol=symbol)
    return PaperTradeListResponse(
        count=len(trades),
        items=[PaperTradeResponse.model_validate(_trade_data(trade)) for trade in trades],
    )


@router.get("/{trade_id}", response_model=PaperTradeResponse, response_model_by_alias=True)
def get_paper_trade(
    trade_id: UUID,
    repository: Annotated[PaperTradeRepository, Depends(get_paper_trade_repository)],
) -> PaperTradeResponse:
    trade = repository.get(trade_id)
    if trade is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paper trade not found.")
    return PaperTradeResponse.model_validate(_trade_data(trade))


@router.post(
    "/{trade_id}/market-price",
    response_model=PaperTradeResponse,
    response_model_by_alias=True,
)
def observe_market_price(
    trade_id: UUID,
    payload: PaperTradePriceRequest,
    service: Annotated[PaperTradingService, Depends(get_paper_trading_service)],
) -> PaperTradeResponse:
    return _transition_response(
        lambda: service.observe_price(
            trade_id,
            price=payload.price,
            occurred_at=payload.occurred_at,
        )
    )


@router.post(
    "/{trade_id}/close",
    response_model=PaperTradeResponse,
    response_model_by_alias=True,
)
def close_paper_trade(
    trade_id: UUID,
    payload: PaperTradeCloseRequest,
    service: Annotated[PaperTradingService, Depends(get_paper_trading_service)],
) -> PaperTradeResponse:
    return _transition_response(
        lambda: service.close_trade(
            trade_id,
            exit_price=payload.exit_price,
            closed_at=payload.closed_at,
        )
    )


@router.post(
    "/{trade_id}/cancel",
    response_model=PaperTradeResponse,
    response_model_by_alias=True,
)
def cancel_paper_trade(
    trade_id: UUID,
    payload: PaperTradeCancelRequest,
    service: Annotated[PaperTradingService, Depends(get_paper_trading_service)],
) -> PaperTradeResponse:
    return _transition_response(
        lambda: service.cancel_trade(trade_id, cancelled_at=payload.cancelled_at)
    )


@router.get(
    "/{trade_id}/events",
    response_model=PaperTradeEventListResponse,
    response_model_by_alias=True,
)
def list_paper_trade_events(
    trade_id: UUID,
    repository: Annotated[PaperTradeRepository, Depends(get_paper_trade_repository)],
) -> PaperTradeEventListResponse:
    if repository.get(trade_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paper trade not found.")
    events = repository.list_events(trade_id)
    return PaperTradeEventListResponse(
        count=len(events),
        items=[_event_response(event) for event in events],
    )


def _transition_response(operation: Callable[[], PaperTrade]) -> PaperTradeResponse:
    try:
        trade = operation()
    except PaperTradeNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except PaperTradeTransitionError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except PaperTradeRevisionConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    return PaperTradeResponse.model_validate(_trade_data(trade))


def _trade_data(trade: PaperTrade) -> dict[str, Any]:
    return {
        "tradeId": trade.trade_id,
        "setupId": trade.setup_id,
        "eventId": trade.event_id,
        "symbol": trade.symbol,
        "exchange": trade.exchange,
        "timeframe": trade.timeframe,
        "direction": trade.direction,
        "session": trade.session,
        "strategyVersion": trade.strategy_version,
        "status": trade.status,
        "entryPrice": trade.entry_price,
        "stopLoss": trade.stop_loss,
        "takeProfit": trade.take_profit,
        "plannedRiskReward": trade.planned_risk_reward,
        "accountBalance": trade.account_balance,
        "riskPercent": trade.risk_percent,
        "riskAmount": trade.risk_amount,
        "quantity": trade.quantity,
        "openedAt": trade.opened_at,
        "closedAt": trade.closed_at,
        "exitPrice": trade.exit_price,
        "exitReason": trade.exit_reason,
        "realizedPnl": trade.realized_pnl,
        "realizedR": trade.realized_r,
        "riskPolicyVersion": trade.risk_policy_version,
        "createdAt": trade.created_at,
        "updatedAt": trade.updated_at,
        "revision": trade.revision,
    }


def _event_response(event: PaperTradeEvent) -> PaperTradeEventResponse:
    return PaperTradeEventResponse.model_validate(
        {
            "tradeId": event.trade_id,
            "sequence": event.sequence,
            "eventType": event.event_type,
            "occurredAt": event.occurred_at,
            "details": event.details,
        }
    )
