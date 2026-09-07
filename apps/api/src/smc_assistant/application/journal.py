from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from pydantic import TypeAdapter

from smc_assistant.application.outcome_records import OutcomeRecord, OutcomeRepository
from smc_assistant.application.setup_candidates import (
    SetupCandidateRecord,
    SetupCandidateRepository,
)
from smc_assistant.application.webhook_ingestion import WebhookEventRepository
from smc_assistant.contracts.journal import JournalContentRequest, JournalCreateRequest
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.journal import JournalExecutionStatus

_setup_adapter = TypeAdapter(SetupCandidateRecord)
_outcome_adapter = TypeAdapter(OutcomeRecord)


class JournalError(ValueError):
    pass


class JournalSetupNotFoundError(JournalError):
    pass


class JournalOutcomeNotFoundError(JournalError):
    pass


class JournalOutcomeMismatchError(JournalError):
    pass


class JournalAlreadyExistsError(JournalError):
    pass


class JournalNotFoundError(JournalError):
    pass


class JournalRevisionConflictError(JournalError):
    pass


@dataclass(frozen=True, slots=True)
class JournalEntry:
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
    setup_snapshot: dict[str, Any]
    outcome_snapshot: dict[str, Any] | None
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
    tags: tuple[str, ...]
    revision: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        for value in (self.signal_time, self.created_at, self.updated_at):
            if value.utcoffset() is None:
                raise ValueError("Journal timestamps must be timezone-aware.")
        if self.revision < 1:
            raise ValueError("Journal revision must be positive.")


class JournalRepository(Protocol):
    def create(self, entry: JournalEntry) -> JournalEntry:
        pass

    def get(self, journal_id: UUID) -> JournalEntry | None:
        pass

    def get_by_setup_id(self, setup_id: str) -> JournalEntry | None:
        pass

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        execution_status: JournalExecutionStatus | None = None,
    ) -> list[JournalEntry]:
        pass

    def update(self, entry: JournalEntry, *, expected_revision: int) -> JournalEntry:
        pass

    def list_revisions(self, journal_id: UUID) -> list[JournalEntry]:
        pass


def create_journal_entry(
    setup_id: str,
    content: JournalCreateRequest,
    *,
    setup_repository: SetupCandidateRepository,
    webhook_repository: WebhookEventRepository,
    outcome_repository: OutcomeRepository,
    journal_repository: JournalRepository,
    now: datetime | None = None,
) -> JournalEntry:
    setup = setup_repository.get_by_setup_id(setup_id)
    if setup is None:
        raise JournalSetupNotFoundError("Setup candidate not found.")
    webhook = webhook_repository.get_by_event_id(setup.event_id)
    if webhook is None:
        raise JournalSetupNotFoundError("Setup source event not found.")
    payload = TradingViewWebhookPayload.model_validate(webhook.payload)
    outcome = _resolve_outcome(content.outcome_id, setup, outcome_repository)
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    outcome_result = outcome.evaluation.outcome if outcome is not None else None
    excursion = outcome_result.excursion if outcome_result is not None else None
    entry = JournalEntry(
        journal_id=uuid4(),
        setup_id=setup.setup_id,
        outcome_id=outcome.outcome_id if outcome is not None else None,
        event_id=setup.event_id,
        symbol=setup.symbol,
        exchange=setup.exchange,
        timeframe=setup.timeframe,
        direction=setup.direction,
        session=payload.features.session.value,
        strategy_version=setup.strategy_version,
        signal_time=payload.bar_close_time.astimezone(UTC),
        setup_snapshot={
            "candidate": _setup_adapter.dump_python(setup, mode="json"),
            "sourcePayload": payload.model_dump(mode="json", by_alias=True),
        },
        outcome_snapshot=(
            _outcome_adapter.dump_python(outcome, mode="json") if outcome is not None else None
        ),
        outcome_label=outcome_result.label.value if outcome_result is not None else None,
        realized_r=outcome_result.net_realized_r if outcome_result is not None else None,
        mfe_r=excursion.mfe_r if excursion is not None else None,
        mae_r=excursion.mae_r if excursion is not None else None,
        execution_status=content.execution_status,
        user_note=content.user_note,
        screenshot_reference=content.screenshot_reference,
        manual_rating=content.manual_rating,
        manual_override=content.manual_override,
        override_reason=content.override_reason,
        tags=tuple(content.tags),
        revision=1,
        created_at=timestamp,
        updated_at=timestamp,
    )
    return journal_repository.create(entry)


def update_journal_entry(
    journal_id: UUID,
    content: JournalContentRequest,
    *,
    expected_revision: int,
    journal_repository: JournalRepository,
    now: datetime | None = None,
) -> JournalEntry:
    existing = journal_repository.get(journal_id)
    if existing is None:
        raise JournalNotFoundError("Journal entry not found.")
    if existing.revision != expected_revision:
        raise JournalRevisionConflictError("Journal entry was modified by another request.")
    timestamp = (now or datetime.now(UTC)).astimezone(UTC)
    updated = replace(
        existing,
        execution_status=content.execution_status,
        user_note=content.user_note,
        screenshot_reference=content.screenshot_reference,
        manual_rating=content.manual_rating,
        manual_override=content.manual_override,
        override_reason=content.override_reason,
        tags=tuple(content.tags),
        revision=existing.revision + 1,
        updated_at=timestamp,
    )
    return journal_repository.update(updated, expected_revision=expected_revision)


def _resolve_outcome(
    outcome_id: UUID | None,
    setup: SetupCandidateRecord,
    repository: OutcomeRepository,
) -> OutcomeRecord | None:
    if outcome_id is None:
        matches = repository.list_recent(limit=1, event_id=setup.event_id)
        return matches[0] if matches else None
    outcome = repository.get_by_outcome_id(outcome_id)
    if outcome is None:
        raise JournalOutcomeNotFoundError("Outcome not found.")
    if outcome.evaluation.event_id != setup.event_id:
        raise JournalOutcomeMismatchError("Outcome does not belong to the selected setup.")
    return outcome
