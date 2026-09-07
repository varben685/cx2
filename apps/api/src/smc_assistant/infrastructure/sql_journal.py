from typing import Any, cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import Engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.journal import (
    JournalAlreadyExistsError,
    JournalEntry,
    JournalNotFoundError,
    JournalRevisionConflictError,
)
from smc_assistant.domain.journal import JournalExecutionStatus
from smc_assistant.infrastructure.webhook_event_schema import (
    journal_entries,
    journal_entry_revisions,
)

_entry_adapter = TypeAdapter(JournalEntry)


def _snapshot(entry: JournalEntry) -> dict[str, Any]:
    return cast(dict[str, Any], _entry_adapter.dump_python(entry, mode="json"))


def _entry_values(entry: JournalEntry) -> dict[str, Any]:
    return {
        "journal_id": entry.journal_id,
        "setup_id": entry.setup_id,
        "outcome_id": entry.outcome_id,
        "symbol": entry.symbol,
        "execution_status": entry.execution_status.value,
        "revision": entry.revision,
        "updated_at": entry.updated_at,
        "snapshot": _snapshot(entry),
    }


def _revision_values(entry: JournalEntry) -> dict[str, Any]:
    return {
        "journal_id": entry.journal_id,
        "revision": entry.revision,
        "created_at": entry.updated_at,
        "snapshot": _snapshot(entry),
    }


class SQLJournalRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, entry: JournalEntry) -> JournalEntry:
        try:
            with self._engine.begin() as connection:
                connection.execute(insert(journal_entries).values(**_entry_values(entry)))
                connection.execute(
                    insert(journal_entry_revisions).values(**_revision_values(entry))
                )
        except IntegrityError as error:
            if self.get_by_setup_id(entry.setup_id) is not None:
                raise JournalAlreadyExistsError(
                    "A journal entry already exists for this setup."
                ) from error
            raise
        return entry

    def get(self, journal_id: UUID) -> JournalEntry | None:
        query = select(journal_entries.c.snapshot).where(
            journal_entries.c.journal_id == journal_id
        )
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _entry_adapter.validate_python(snapshot) if snapshot is not None else None

    def get_by_setup_id(self, setup_id: str) -> JournalEntry | None:
        query = select(journal_entries.c.snapshot).where(
            journal_entries.c.setup_id == setup_id
        )
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _entry_adapter.validate_python(snapshot) if snapshot is not None else None

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        execution_status: JournalExecutionStatus | None = None,
    ) -> list[JournalEntry]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        query = select(journal_entries.c.snapshot)
        if symbol is not None:
            query = query.where(journal_entries.c.symbol == symbol)
        if execution_status is not None:
            query = query.where(
                journal_entries.c.execution_status == execution_status.value
            )
        query = query.order_by(
            journal_entries.c.updated_at.desc(), journal_entries.c.journal_id.desc()
        ).limit(limit)
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_entry_adapter.validate_python(snapshot) for snapshot in snapshots]

    def update(self, entry: JournalEntry, *, expected_revision: int) -> JournalEntry:
        with self._engine.begin() as connection:
            current_snapshot = connection.execute(
                select(journal_entries.c.snapshot)
                .where(journal_entries.c.journal_id == entry.journal_id)
                .with_for_update()
            ).scalar_one_or_none()
            if current_snapshot is None:
                raise JournalNotFoundError("Journal entry not found.")
            current = _entry_adapter.validate_python(current_snapshot)
            if current.revision != expected_revision:
                raise JournalRevisionConflictError(
                    "Journal entry was modified by another request."
                )
            if entry.revision != expected_revision + 1:
                raise ValueError("Updated journal revision must increment by one.")
            connection.execute(
                update(journal_entries)
                .where(journal_entries.c.journal_id == entry.journal_id)
                .values(**_entry_values(entry))
            )
            connection.execute(
                insert(journal_entry_revisions).values(**_revision_values(entry))
            )
        return entry

    def list_revisions(self, journal_id: UUID) -> list[JournalEntry]:
        query = (
            select(journal_entry_revisions.c.snapshot)
            .where(journal_entry_revisions.c.journal_id == journal_id)
            .order_by(journal_entry_revisions.c.revision)
        )
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_entry_adapter.validate_python(snapshot) for snapshot in snapshots]
