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
