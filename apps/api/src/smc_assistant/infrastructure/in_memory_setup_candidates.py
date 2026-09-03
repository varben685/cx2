from threading import Lock

from smc_assistant.application.setup_candidates import (
    SetupCandidateRecord,
    SetupCandidateSaveResult,
)


class InMemorySetupCandidateRepository:
    def __init__(self) -> None:
        self._records_by_event_id: dict[str, SetupCandidateRecord] = {}
        self._lock = Lock()

    def save_if_absent(self, record: SetupCandidateRecord) -> SetupCandidateSaveResult:
        with self._lock:
            existing_record = self._records_by_event_id.get(record.event_id)
            if existing_record is not None:
                return SetupCandidateSaveResult(record=existing_record, created=False)

            self._records_by_event_id[record.event_id] = record
            return SetupCandidateSaveResult(record=record, created=True)

    def get_by_event_id(self, event_id: str) -> SetupCandidateRecord | None:
        with self._lock:
            return self._records_by_event_id.get(event_id)

    def get_by_setup_id(self, setup_id: str) -> SetupCandidateRecord | None:
        with self._lock:
            return next(
                (
                    record
                    for record in self._records_by_event_id.values()
                    if record.setup_id == setup_id
                ),
                None,
            )

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        accepted: bool | None = None,
    ) -> list[SetupCandidateRecord]:
        with self._lock:
            records = list(self._records_by_event_id.values())

        if symbol is not None:
            records = [record for record in records if record.symbol == symbol]

        if accepted is not None:
            records = [record for record in records if record.accepted is accepted]

        return sorted(
            records,
            key=lambda record: (record.received_at, record.setup_id),
            reverse=True,
        )[:limit]
