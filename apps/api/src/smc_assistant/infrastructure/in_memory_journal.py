from threading import Lock
from uuid import UUID

from smc_assistant.application.journal import (
    JournalAlreadyExistsError,
    JournalEntry,
    JournalNotFoundError,
    JournalRevisionConflictError,
)
from smc_assistant.domain.journal import JournalExecutionStatus


class InMemoryJournalRepository:
    def __init__(self) -> None:
        self._entries: dict[UUID, JournalEntry] = {}
        self._journal_ids_by_setup: dict[str, UUID] = {}
        self._revisions: dict[UUID, list[JournalEntry]] = {}
        self._lock = Lock()

    def create(self, entry: JournalEntry) -> JournalEntry:
        with self._lock:
            if entry.setup_id in self._journal_ids_by_setup:
                raise JournalAlreadyExistsError("A journal entry already exists for this setup.")
            if entry.journal_id in self._entries:
                raise JournalAlreadyExistsError("Journal entry ID already exists.")
            self._entries[entry.journal_id] = entry
            self._journal_ids_by_setup[entry.setup_id] = entry.journal_id
            self._revisions[entry.journal_id] = [entry]
            return entry

    def get(self, journal_id: UUID) -> JournalEntry | None:
        with self._lock:
            return self._entries.get(journal_id)

    def get_by_setup_id(self, setup_id: str) -> JournalEntry | None:
        with self._lock:
            journal_id = self._journal_ids_by_setup.get(setup_id)
            return self._entries.get(journal_id) if journal_id is not None else None

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        execution_status: JournalExecutionStatus | None = None,
    ) -> list[JournalEntry]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        with self._lock:
            entries = list(self._entries.values())
        return sorted(
            (
                entry
                for entry in entries
                if (symbol is None or entry.symbol == symbol)
                and (execution_status is None or entry.execution_status == execution_status)
            ),
            key=lambda entry: (entry.updated_at, entry.journal_id),
            reverse=True,
        )[:limit]

    def update(self, entry: JournalEntry, *, expected_revision: int) -> JournalEntry:
        with self._lock:
            existing = self._entries.get(entry.journal_id)
            if existing is None:
                raise JournalNotFoundError("Journal entry not found.")
            if existing.revision != expected_revision:
                raise JournalRevisionConflictError(
                    "Journal entry was modified by another request."
                )
            if entry.revision != expected_revision + 1:
                raise ValueError("Updated journal revision must increment by one.")
            self._entries[entry.journal_id] = entry
            self._revisions[entry.journal_id].append(entry)
            return entry

    def list_revisions(self, journal_id: UUID) -> list[JournalEntry]:
        with self._lock:
            return list(self._revisions.get(journal_id, []))
