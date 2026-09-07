import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema, DropSchema
from test_sql_setup_candidates import (
    setup_candidate_record,
    webhook_record,
)

from smc_assistant.application.journal import (
    JournalAlreadyExistsError,
    JournalEntry,
    JournalRevisionConflictError,
)
from smc_assistant.domain.journal import JournalExecutionStatus
from smc_assistant.infrastructure.database import initialize_database_schema
from smc_assistant.infrastructure.in_memory_journal import InMemoryJournalRepository
from smc_assistant.infrastructure.sql_journal import SQLJournalRepository
from smc_assistant.infrastructure.sql_setup_candidates import SQLSetupCandidateRepository
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository

BACKENDS = ["memory", "sqlite"]
if os.environ.get("TEST_POSTGRES_URL"):
    BACKENDS.append("postgres")


@pytest.fixture(params=BACKENDS)
def repository(request):
    if request.param == "memory":
        yield InMemoryJournalRepository()
        return
    if request.param == "postgres":
        engine = create_engine(os.environ["TEST_POSTGRES_URL"])
        schema = f"test_journal_{uuid4().hex}"
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        scoped_engine = engine.execution_options(schema_translate_map={None: schema})
        try:
            initialize_database_schema(scoped_engine)
            yield SQLJournalRepository(scoped_engine)
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
            engine.dispose()
        return

    engine = create_engine("sqlite+pysqlite:///:memory:")
    initialize_database_schema(engine)
    try:
        yield SQLJournalRepository(engine)
    finally:
        engine.dispose()


def journal_entry(
    *,
    journal_id: UUID | None = None,
    setup_id: str = "setup-001",
    symbol: str = "BTCUSDT",
    updated_at: datetime | None = None,
) -> JournalEntry:
    timestamp = updated_at or datetime(2026, 9, 7, 20, 0, tzinfo=UTC)
    return JournalEntry(
        journal_id=journal_id or uuid4(),
        setup_id=setup_id,
        outcome_id=None,
        event_id=setup_id,
        symbol=symbol,
        exchange="BINANCE",
        timeframe="1",
        direction="LONG",
        session="NEW_YORK",
        strategy_version="smc-rce-v1",
        signal_time=datetime(2026, 9, 7, 19, 55, tzinfo=UTC),
        setup_snapshot={"sourcePayload": {"eventId": setup_id}},
        outcome_snapshot=None,
        outcome_label=None,
        realized_r=None,
        mfe_r=None,
        mae_r=None,
        execution_status=JournalExecutionStatus.TAKEN,
        user_note="Initial note",
        screenshot_reference=None,
        manual_rating=4,
        manual_override=False,
        override_reason=None,
        tags=("A+",),
        revision=1,
        created_at=timestamp,
        updated_at=timestamp,
    )


def seed_setup(repository, setup_id: str, symbol: str) -> None:
    if not isinstance(repository, SQLJournalRepository):
        return
    webhook_repository = SQLWebhookEventRepository(repository._engine)
    setup_repository = SQLSetupCandidateRepository(repository._engine)
    webhook = webhook_record(event_id=setup_id)
    candidate = replace(setup_candidate_record(event_id=setup_id), symbol=symbol)
    webhook_repository.save_if_absent(webhook)
    setup_repository.save_if_absent(candidate)


def test_round_trip_update_history_and_filters(repository) -> None:
    first = journal_entry(journal_id=UUID(int=1))
    second = journal_entry(
        journal_id=UUID(int=2),
        setup_id="setup-002",
        symbol="ETHUSDT",
        updated_at=first.updated_at + timedelta(minutes=1),
    )
    seed_setup(repository, first.setup_id, first.symbol)
    seed_setup(repository, second.setup_id, second.symbol)
    assert repository.create(first) == first
    repository.create(second)
    assert repository.get(first.journal_id) == first
    assert repository.get_by_setup_id(first.setup_id) == first
    assert repository.list_recent(limit=1) == [second]
    assert repository.list_recent(symbol="BTCUSDT") == [first]
    assert repository.list_recent(execution_status=JournalExecutionStatus.TAKEN) == [
        second,
        first,
    ]

    updated = replace(
        first,
        execution_status=JournalExecutionStatus.SKIPPED,
        user_note="Updated note",
        revision=2,
        updated_at=first.updated_at + timedelta(minutes=2),
    )
    assert repository.update(updated, expected_revision=1) == updated
    assert repository.get(first.journal_id) == updated
    assert repository.list_revisions(first.journal_id) == [first, updated]
    assert repository.list_recent(execution_status=JournalExecutionStatus.SKIPPED) == [updated]


def test_rejects_duplicate_setup_and_stale_update(repository) -> None:
    first = journal_entry()
    seed_setup(repository, first.setup_id, first.symbol)
    repository.create(first)
    with pytest.raises(JournalAlreadyExistsError):
        repository.create(journal_entry(setup_id=first.setup_id))
    updated = replace(first, revision=2, updated_at=first.updated_at + timedelta(minutes=1))
    with pytest.raises(JournalRevisionConflictError):
        repository.update(updated, expected_revision=2)
    assert repository.list_revisions(first.journal_id) == [first]
