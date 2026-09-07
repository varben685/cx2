from datetime import datetime
from typing import Annotated, Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from smc_assistant.application.journal import (
    JournalAlreadyExistsError,
    JournalEntry,
    JournalNotFoundError,
    JournalOutcomeMismatchError,
    JournalOutcomeNotFoundError,
    JournalRepository,
    JournalRevisionConflictError,
    JournalSetupNotFoundError,
    create_journal_entry,
    update_journal_entry,
)
from smc_assistant.application.outcome_records import OutcomeRepository
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.webhook_ingestion import WebhookEventRepository
from smc_assistant.contracts.journal import JournalCreateRequest, JournalUpdateRequest
from smc_assistant.domain.journal import JournalExecutionStatus

router = APIRouter(tags=["journal"])


class CamelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class JournalSummaryResponse(CamelResponse):
    journal_id: UUID
    setup_id: str
    outcome_id: UUID | None
    event_id: str
    symbol: str
    exchange: str
    timeframe: str
    direction: str
    session: str
    strategy_version: str
    signal_time: datetime
    outcome_label: str | None
    realized_r: float | None
    mfe_r: float | None
    mae_r: float | None
    execution_status: JournalExecutionStatus
    user_note: str | None
    screenshot_reference: str | None
    manual_rating: int | None
    manual_override: bool
    override_reason: str | None
    tags: list[str]
    revision: int
    created_at: datetime
    updated_at: datetime


class JournalDetailResponse(JournalSummaryResponse):
    setup_snapshot: dict[str, Any]
    outcome_snapshot: dict[str, Any] | None


class JournalListResponse(CamelResponse):
    count: int
    items: list[JournalSummaryResponse]


class JournalRevisionListResponse(CamelResponse):
    count: int
    items: list[JournalSummaryResponse]


def get_journal_repository(request: Request) -> JournalRepository:
    return cast(JournalRepository, request.app.state.journal_repository)


def get_setup_repository(request: Request) -> SetupCandidateRepository:
    return cast(SetupCandidateRepository, request.app.state.setup_candidate_repository)


def get_webhook_repository(request: Request) -> WebhookEventRepository:
    return cast(WebhookEventRepository, request.app.state.webhook_event_repository)


def get_outcome_repository(request: Request) -> OutcomeRepository:
    return cast(OutcomeRepository, request.app.state.outcome_repository)


@router.post(
    "/api/v1/setups/{setup_id}/journal",
    response_model=JournalDetailResponse,
    status_code=201,
)
def create_setup_journal(
    setup_id: str,
    payload: JournalCreateRequest,
    setup_repository: Annotated[SetupCandidateRepository, Depends(get_setup_repository)],
    webhook_repository: Annotated[WebhookEventRepository, Depends(get_webhook_repository)],
    outcome_repository: Annotated[OutcomeRepository, Depends(get_outcome_repository)],
    journal_repository: Annotated[JournalRepository, Depends(get_journal_repository)],
) -> JournalDetailResponse:
    try:
        entry = create_journal_entry(
            setup_id,
            payload,
            setup_repository=setup_repository,
            webhook_repository=webhook_repository,
            outcome_repository=outcome_repository,
            journal_repository=journal_repository,
        )
    except JournalSetupNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except JournalOutcomeNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except JournalOutcomeMismatchError as error:
        raise HTTPException(422, str(error)) from error
    except JournalAlreadyExistsError as error:
        raise HTTPException(409, str(error)) from error
    return _detail_response(entry)


@router.get("/api/v1/journal", response_model=JournalListResponse)
def list_journal_entries(
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    symbol: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    execution_status: Annotated[
        JournalExecutionStatus | None,
        Query(alias="executionStatus"),
    ] = None,
) -> JournalListResponse:
    entries = repository.list_recent(
        limit=limit,
        symbol=symbol,
        execution_status=execution_status,
    )
    return JournalListResponse(
        count=len(entries),
        items=[_summary_response(entry) for entry in entries],
    )


@router.get("/api/v1/journal/{journal_id}", response_model=JournalDetailResponse)
def get_journal_entry(
    journal_id: UUID,
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
) -> JournalDetailResponse:
    entry = repository.get(journal_id)
    if entry is None:
        raise HTTPException(404, "Journal entry not found.")
    return _detail_response(entry)


@router.put("/api/v1/journal/{journal_id}", response_model=JournalDetailResponse)
def update_journal(
    journal_id: UUID,
    payload: JournalUpdateRequest,
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
) -> JournalDetailResponse:
    try:
        entry = update_journal_entry(
            journal_id,
            payload,
            expected_revision=payload.expected_revision,
            journal_repository=repository,
        )
    except JournalNotFoundError as error:
        raise HTTPException(404, str(error)) from error
    except JournalRevisionConflictError as error:
        raise HTTPException(409, str(error)) from error
    return _detail_response(entry)


@router.get(
    "/api/v1/journal/{journal_id}/revisions",
    response_model=JournalRevisionListResponse,
)
def list_journal_revisions(
    journal_id: UUID,
    repository: Annotated[JournalRepository, Depends(get_journal_repository)],
) -> JournalRevisionListResponse:
    if repository.get(journal_id) is None:
        raise HTTPException(404, "Journal entry not found.")
    revisions = repository.list_revisions(journal_id)
    return JournalRevisionListResponse(
        count=len(revisions),
        items=[_summary_response(entry) for entry in revisions],
    )


def _summary_response(entry: JournalEntry) -> JournalSummaryResponse:
    return JournalSummaryResponse(
        journal_id=entry.journal_id,
        setup_id=entry.setup_id,
        outcome_id=entry.outcome_id,
        event_id=entry.event_id,
        symbol=entry.symbol,
        exchange=entry.exchange,
        timeframe=entry.timeframe,
        direction=entry.direction,
        session=entry.session,
        strategy_version=entry.strategy_version,
        signal_time=entry.signal_time,
        outcome_label=entry.outcome_label,
        realized_r=entry.realized_r,
        mfe_r=entry.mfe_r,
        mae_r=entry.mae_r,
        execution_status=entry.execution_status,
        user_note=entry.user_note,
        screenshot_reference=entry.screenshot_reference,
        manual_rating=entry.manual_rating,
        manual_override=entry.manual_override,
        override_reason=entry.override_reason,
        tags=list(entry.tags),
        revision=entry.revision,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _detail_response(entry: JournalEntry) -> JournalDetailResponse:
    return JournalDetailResponse(
        **_summary_response(entry).model_dump(),
        setup_snapshot=entry.setup_snapshot,
        outcome_snapshot=entry.outcome_snapshot,
    )
