from smc_assistant.application.audit import NoopAuditLogger
from smc_assistant.application.webhook_ingestion import WebhookIngestionService
from smc_assistant.config import Settings
from smc_assistant.infrastructure.webhook_ingestion_factory import (
    create_webhook_ingestion_service,
)


def test_factory_uses_memory_repository_by_default() -> None:
    service = create_webhook_ingestion_service(Settings(), NoopAuditLogger())

    assert isinstance(service, WebhookIngestionService)
