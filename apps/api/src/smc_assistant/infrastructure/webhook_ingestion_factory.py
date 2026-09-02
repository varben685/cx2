from smc_assistant.application.audit import AuditLogger
from smc_assistant.application.webhook_ingestion import WebhookIngestionService
from smc_assistant.config import Settings
from smc_assistant.infrastructure.database import (
    create_database_engine,
    initialize_database_schema,
)
from smc_assistant.infrastructure.in_memory_webhook_events import (
    InMemoryWebhookEventRepository,
)
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository


def create_webhook_ingestion_service(
    settings: Settings,
    audit_logger: AuditLogger,
) -> WebhookIngestionService:
    if settings.webhook_event_repository == "postgres":
        engine = create_database_engine(settings.database_url)
        initialize_database_schema(engine)
        return WebhookIngestionService(SQLWebhookEventRepository(engine), audit_logger)

    return WebhookIngestionService(InMemoryWebhookEventRepository(), audit_logger)
