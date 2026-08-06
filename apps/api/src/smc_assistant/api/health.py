from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

from smc_assistant import __version__

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="smc-assistant-api",
        version=__version__,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    return HealthResponse(
        status="ready",
        service="smc-assistant-api",
        version=__version__,
        timestamp=datetime.now(UTC),
    )

