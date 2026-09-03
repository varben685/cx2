from smc_assistant.application.audit import NoopAuditLogger
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.webhook_ingestion import WebhookIngestionService
from smc_assistant.config import Settings
from smc_assistant.infrastructure.webhook_ingestion_factory import (
    create_webhook_ingestion_service,
    create_webhook_ingestion_services,
)


def test_factory_uses_memory_repository_by_default() -> None:
    service = create_webhook_ingestion_service(Settings(), NoopAuditLogger())

    assert isinstance(service, WebhookIngestionService)


def test_factory_exposes_same_setup_candidate_repository_for_reads() -> None:
    services = create_webhook_ingestion_services(Settings(), NoopAuditLogger())

    assert isinstance(services.webhook_ingestion_service, WebhookIngestionService)
    assert isinstance(services.setup_candidate_repository, SetupCandidateRepository)
