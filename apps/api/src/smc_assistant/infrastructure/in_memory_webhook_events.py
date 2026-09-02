from threading import Lock

from smc_assistant.application.webhook_ingestion import (
    WebhookEventRecord,
    WebhookEventSaveResult,
)


class InMemoryWebhookEventRepository:
    def __init__(self) -> None:
        self._records_by_event_id: dict[str, WebhookEventRecord] = {}
        self._lock = Lock()

    def save_if_absent(self, record: WebhookEventRecord) -> WebhookEventSaveResult:
        with self._lock:
            existing_record = self._records_by_event_id.get(record.event_id)
            if existing_record is not None:
                return WebhookEventSaveResult(record=existing_record, created=False)

            self._records_by_event_id[record.event_id] = record
            return WebhookEventSaveResult(record=record, created=True)

    def get_by_event_id(self, event_id: str) -> WebhookEventRecord | None:
        with self._lock:
            return self._records_by_event_id.get(event_id)
