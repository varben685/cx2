from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.application.webhook_ingestion import (
    WebhookIngestionService,
    WebhookIngestionStatus,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
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
    setup_score: SetupScoreResponse = Field(alias="setupScore")
    message: str


def get_webhook_ingestion_service(request: Request) -> WebhookIngestionService:
    return cast(WebhookIngestionService, request.app.state.webhook_ingestion_service)


@router.post(
    "/tradingview",
    response_model=TradingViewWebhookResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_tradingview_webhook(
    payload: TradingViewWebhookPayload,
    ingestion_service: Annotated[
        WebhookIngestionService,
        Depends(get_webhook_ingestion_service),
    ],
) -> TradingViewWebhookResponse:
    result = ingestion_service.ingest_tradingview(payload)
    return TradingViewWebhookResponse.model_validate(
        {
            "status": result.status,
            "eventId": result.event_id,
            "eventType": result.event_type,
            "schemaVersion": result.schema_version,
            "receivedAt": result.received_at.isoformat(),
            "firstReceivedAt": result.first_received_at.isoformat(),
            "setupScore": _setup_score_response(result.setup_score),
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
