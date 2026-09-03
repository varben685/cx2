from dataclasses import dataclass

from smc_assistant.application.audit import AuditLogger
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.webhook_ingestion import WebhookIngestionService
from smc_assistant.config import Settings
from smc_assistant.infrastructure.database import (
    create_database_engine,
    initialize_database_schema,
)
from smc_assistant.infrastructure.in_memory_setup_candidates import (
    InMemorySetupCandidateRepository,
)
from smc_assistant.infrastructure.in_memory_webhook_events import (
    InMemoryWebhookEventRepository,
)
from smc_assistant.infrastructure.sql_setup_candidates import SQLSetupCandidateRepository
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository


@dataclass(frozen=True, slots=True)
class WebhookIngestionServices:
    webhook_ingestion_service: WebhookIngestionService
    setup_candidate_repository: SetupCandidateRepository


def create_webhook_ingestion_service(
    settings: Settings,
    audit_logger: AuditLogger,
) -> WebhookIngestionService:
    return create_webhook_ingestion_services(
        settings,
        audit_logger,
    ).webhook_ingestion_service


def create_webhook_ingestion_services(
    settings: Settings,
    audit_logger: AuditLogger,
) -> WebhookIngestionServices:
    if settings.webhook_event_repository == "postgres":
        engine = create_database_engine(settings.database_url)
        initialize_database_schema(engine)
        setup_candidate_repository: SetupCandidateRepository = SQLSetupCandidateRepository(engine)
        return WebhookIngestionServices(
            webhook_ingestion_service=WebhookIngestionService(
                SQLWebhookEventRepository(engine),
                audit_logger,
                setup_candidate_repository=setup_candidate_repository,
            ),
            setup_candidate_repository=setup_candidate_repository,
        )

    setup_candidate_repository = InMemorySetupCandidateRepository()
    return WebhookIngestionServices(
        webhook_ingestion_service=WebhookIngestionService(
            InMemoryWebhookEventRepository(),
            audit_logger,
            setup_candidate_repository=setup_candidate_repository,
        ),
        setup_candidate_repository=setup_candidate_repository,
    )
