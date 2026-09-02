from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.application.webhook_ingestion import (
    WebhookIngestionService,
    WebhookIngestionStatus,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class TradingViewWebhookResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: WebhookIngestionStatus
    event_id: str = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    schema_version: str = Field(alias="schemaVersion")
    received_at: str = Field(alias="receivedAt")
    first_received_at: str = Field(alias="firstReceivedAt")
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
            "message": result.message,
        }
    )
