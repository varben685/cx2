from threading import Lock
from uuid import UUID

from smc_assistant.application.outcome_records import OutcomeRecord, OutcomeSaveResult


class InMemoryOutcomeRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, OutcomeRecord] = {}
        self._keys: dict[tuple[UUID, str], UUID] = {}
        self._lock = Lock()

    def save_if_absent(self, record: OutcomeRecord) -> OutcomeSaveResult:
        key = (record.run_id, record.evaluation.event_id)
        with self._lock:
            existing_id = self._keys.get(key)
            if existing_id is not None:
                return OutcomeSaveResult(record=self._records[existing_id], created=False)
            if record.outcome_id in self._records:
                raise ValueError("outcome_id already belongs to another run/event.")
            self._records[record.outcome_id] = record
            self._keys[key] = record.outcome_id
            return OutcomeSaveResult(record=record, created=True)

    def get_by_outcome_id(self, outcome_id: UUID) -> OutcomeRecord | None:
        with self._lock:
            return self._records.get(outcome_id)

    def get_by_run_event(self, run_id: UUID, event_id: str) -> OutcomeRecord | None:
        with self._lock:
            outcome_id = self._keys.get((run_id, event_id))
            return self._records.get(outcome_id) if outcome_id is not None else None

    def list_for_run(self, run_id: UUID, *, symbol: str | None = None) -> list[OutcomeRecord]:
        with self._lock:
            return sorted(
                (
                    record
                    for record in self._records.values()
                    if record.run_id == run_id
                    and (symbol is None or record.evaluation.symbol == symbol)
                ),
                key=lambda record: record.outcome_id,
            )

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_id: UUID | None = None,
        event_id: str | None = None,
        symbol: str | None = None,
    ) -> list[OutcomeRecord]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        with self._lock:
            records = list(self._records.values())
        return sorted(
            (
                record
                for record in records
                if (run_id is None or record.run_id == run_id)
                and (event_id is None or record.evaluation.event_id == event_id)
                and (symbol is None or record.evaluation.symbol == symbol)
            ),
            key=lambda record: (record.evaluated_at, record.outcome_id),
            reverse=True,
        )[:limit]
