from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class WebhookProcessingStatus(StrEnum):
    VALIDATED = "VALIDATED"


class TradingViewWebhookResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: WebhookProcessingStatus
    event_id: str = Field(alias="eventId")
    event_type: str = Field(alias="eventType")
    schema_version: str = Field(alias="schemaVersion")
    received_at: datetime = Field(alias="receivedAt")
    message: str


@router.post(
    "/tradingview",
    response_model=TradingViewWebhookResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
)
def receive_tradingview_webhook(
    payload: TradingViewWebhookPayload,
) -> TradingViewWebhookResponse:
    return TradingViewWebhookResponse.model_validate(
        {
            "status": WebhookProcessingStatus.VALIDATED,
            "eventId": payload.event_id,
            "eventType": payload.event_type,
            "schemaVersion": payload.schema_version,
            "receivedAt": datetime.now(UTC),
            "message": "TradingView webhook payload accepted for processing.",
        }
    )
