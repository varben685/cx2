from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.application.tradingview_live import (
    PaperTradeAutomationStatus,
    TradingViewLiveService,
)
from smc_assistant.application.webhook_ingestion import (
    WebhookEventConflictError,
    WebhookIngestionStatus,
)
from smc_assistant.contracts.tradingview import (
    TradingViewIncomingPayload,
    TradingViewMarketPricePayload,
)
from smc_assistant.domain.paper_trading import PaperTradeStatus
from smc_assistant.domain.setup_scoring import ScoreComponent, SetupScore

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class ScoreComponentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    score: float
    max_score: float = Field(alias="maxScore")
    reason: str


class SetupScoreResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    score: float
    accepted: bool
    strategy_version: str = Field(alias="strategyVersion")
    config_version: str = Field(alias="configVersion")
    components: list[ScoreComponentResponse]
    rejection_reasons: list[str] = Field(alias="rejectionReasons")
    positive_reasons: list[str] = Field(alias="positiveReasons")
    negative_reasons: list[str] = Field(alias="negativeReasons")


class TradingViewWebhookResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: WebhookIngestionStatus
    event_id: str = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    schema_version: str = Field(alias="schemaVersion")
    received_at: str = Field(alias="receivedAt")
    first_received_at: str = Field(alias="firstReceivedAt")
    setup_candidate_id: str = Field(alias="setupCandidateId")
    setup_score: SetupScoreResponse = Field(alias="setupScore")
    paper_trade_automation: "PaperTradeAutomationResponse" = Field(
        alias="paperTradeAutomation"
    )
    message: str


class PaperTradeAutomationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: PaperTradeAutomationStatus
    trade_id: UUID | None = Field(alias="tradeId")
    trade_status: PaperTradeStatus | None = Field(alias="tradeStatus")
    message: str


class MarketPriceTradeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    trade_id: UUID = Field(alias="tradeId")
    status: PaperTradeStatus
    revision: int


class TradingViewMarketPriceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: WebhookIngestionStatus
    event_id: str = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    schema_version: str = Field(alias="schemaVersion")
    received_at: str = Field(alias="receivedAt")
    first_received_at: str = Field(alias="firstReceivedAt")
    symbol: str
    exchange: str
    timeframe: str
    observed_at: str = Field(alias="observedAt")
    price: float
    matched_trades: int = Field(alias="matchedTrades")
    updated_trades: list[MarketPriceTradeResponse] = Field(alias="updatedTrades")
    ignored_trade_ids: list[UUID] = Field(alias="ignoredTradeIds")
    message: str


def get_tradingview_live_service(request: Request) -> TradingViewLiveService:
    return cast(TradingViewLiveService, request.app.state.tradingview_live_service)


@router.post(
    "/tradingview",
    response_model=TradingViewWebhookResponse | TradingViewMarketPriceResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_tradingview_webhook(
    payload: TradingViewIncomingPayload,
    live_service: Annotated[
        TradingViewLiveService,
        Depends(get_tradingview_live_service),
    ],
) -> TradingViewWebhookResponse | TradingViewMarketPriceResponse:
    if isinstance(payload, TradingViewMarketPricePayload):
        try:
            market_result = live_service.ingest_market_price(payload)
        except WebhookEventConflictError as error:
            raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
        batch = market_result.batch
        return TradingViewMarketPriceResponse.model_validate(
            {
                "status": market_result.status,
                "eventId": market_result.event_id,
                "eventType": payload.event_type.value,
                "schemaVersion": market_result.schema_version,
                "receivedAt": market_result.received_at.isoformat(),
                "firstReceivedAt": market_result.first_received_at.isoformat(),
                "symbol": market_result.symbol,
                "exchange": market_result.exchange,
                "timeframe": market_result.timeframe,
                "observedAt": market_result.observed_at.isoformat(),
                "price": market_result.price,
                "matchedTrades": len(batch.matched_trade_ids) if batch else 0,
                "updatedTrades": [
                    {
                        "tradeId": trade.trade_id,
                        "status": trade.status,
                        "revision": trade.revision,
                    }
                    for trade in batch.updated_trades
                ]
                if batch
                else [],
                "ignoredTradeIds": list(batch.ignored_trade_ids) if batch else [],
                "message": market_result.message,
            }
        )

    try:
        live_result = live_service.ingest_setup(payload)
    except WebhookEventConflictError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    result = live_result.ingestion
    automated_trade = live_result.automation.trade
    return TradingViewWebhookResponse.model_validate(
        {
            "status": result.status,
            "eventId": result.event_id,
            "eventType": result.event_type,
            "schemaVersion": result.schema_version,
            "receivedAt": result.received_at.isoformat(),
            "firstReceivedAt": result.first_received_at.isoformat(),
            "setupCandidateId": result.setup_candidate_id,
            "setupScore": _setup_score_response(result.setup_score),
            "paperTradeAutomation": {
                "status": live_result.automation.status,
                "tradeId": automated_trade.trade_id if automated_trade else None,
                "tradeStatus": automated_trade.status if automated_trade else None,
                "message": live_result.automation.message,
            },
            "message": result.message,
        }
    )


def _setup_score_response(setup_score: SetupScore) -> dict[str, object]:
    return {
        "score": setup_score.score,
        "accepted": setup_score.accepted,
        "strategyVersion": setup_score.strategy_version,
        "configVersion": setup_score.config_version,
        "components": [
            _score_component_response(component) for component in setup_score.components
        ],
        "rejectionReasons": list(setup_score.rejection_reasons),
        "positiveReasons": list(setup_score.positive_reasons),
        "negativeReasons": list(setup_score.negative_reasons),
    }


def _score_component_response(component: ScoreComponent) -> dict[str, object]:
    return {
        "name": component.name,
        "score": component.score,
        "maxScore": component.max_score,
        "reason": component.reason,
    }
