from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field

from smc_assistant.application.setup_candidates import (
    SetupCandidateRecord,
    SetupCandidateRepository,
)

router = APIRouter(prefix="/api/v1/setups", tags=["setups"])


class SetupCandidateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    setup_id: str = Field(alias="setupId")
    event_id: str = Field(alias="eventId")
    schema_version: str = Field(alias="schemaVersion")
    strategy_version: str = Field(alias="strategyVersion")
    scoring_config_version: str = Field(alias="scoringConfigVersion")
    symbol: str
    exchange: str
    timeframe: str
    direction: str
    htf_bias: str = Field(alias="htfBias")
    score: float
    accepted: bool
    components: list[dict[str, Any]]
    rejection_reasons: list[str] = Field(alias="rejectionReasons")
    positive_reasons: list[str] = Field(alias="positiveReasons")
    negative_reasons: list[str] = Field(alias="negativeReasons")
    bar_close_time: str = Field(alias="barCloseTime")
    received_at: str = Field(alias="receivedAt")


class SetupCandidateListResponse(BaseModel):
    count: int
    items: list[SetupCandidateResponse]


def get_setup_candidate_repository(request: Request) -> SetupCandidateRepository:
    return cast(
        SetupCandidateRepository,
        request.app.state.setup_candidate_repository,
    )


@router.get("", response_model=SetupCandidateListResponse, response_model_by_alias=True)
def list_setup_candidates(
    repository: Annotated[
        SetupCandidateRepository,
        Depends(get_setup_candidate_repository),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    symbol: str | None = None,
    accepted: bool | None = None,
) -> SetupCandidateListResponse:
    records = repository.list_recent(
        limit=limit,
        symbol=symbol,
        accepted=accepted,
    )
    items = [_setup_candidate_response(record) for record in records]
    return SetupCandidateListResponse(count=len(items), items=items)


@router.get(
    "/{setup_id}",
    response_model=SetupCandidateResponse,
    response_model_by_alias=True,
)
def get_setup_candidate(
    setup_id: str,
    repository: Annotated[
        SetupCandidateRepository,
        Depends(get_setup_candidate_repository),
    ],
) -> SetupCandidateResponse:
    record = repository.get_by_setup_id(setup_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setup candidate not found.",
        )

    return _setup_candidate_response(record)


def _setup_candidate_response(record: SetupCandidateRecord) -> SetupCandidateResponse:
    return SetupCandidateResponse.model_validate(
        {
            "setupId": record.setup_id,
            "eventId": record.event_id,
            "schemaVersion": record.schema_version,
            "strategyVersion": record.strategy_version,
            "scoringConfigVersion": record.scoring_config_version,
            "symbol": record.symbol,
            "exchange": record.exchange,
            "timeframe": record.timeframe,
            "direction": record.direction,
            "htfBias": record.htf_bias,
            "score": record.score,
            "accepted": record.accepted,
            "components": record.components,
            "rejectionReasons": record.rejection_reasons,
            "positiveReasons": record.positive_reasons,
            "negativeReasons": record.negative_reasons,
            "barCloseTime": record.bar_close_time.isoformat(),
            "receivedAt": record.received_at.isoformat(),
        }
    )
