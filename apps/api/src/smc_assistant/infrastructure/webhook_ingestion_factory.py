from dataclasses import dataclass

from smc_assistant.application.audit import AuditLogger
from smc_assistant.application.backtests import BacktestRepository
from smc_assistant.application.journal import JournalRepository
from smc_assistant.application.outcome_records import OutcomeRepository
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.webhook_ingestion import (
    WebhookEventRepository,
    WebhookIngestionService,
)
from smc_assistant.config import Settings
from smc_assistant.infrastructure.database import (
    create_database_engine,
    initialize_database_schema,
)
from smc_assistant.infrastructure.in_memory_backtests import InMemoryBacktestRepository
from smc_assistant.infrastructure.in_memory_journal import InMemoryJournalRepository
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository
from smc_assistant.infrastructure.in_memory_setup_candidates import (
    InMemorySetupCandidateRepository,
)
from smc_assistant.infrastructure.in_memory_webhook_events import (
    InMemoryWebhookEventRepository,
)
from smc_assistant.infrastructure.sql_backtests import SQLBacktestRepository
from smc_assistant.infrastructure.sql_journal import SQLJournalRepository
from smc_assistant.infrastructure.sql_outcomes import SQLOutcomeRepository
from smc_assistant.infrastructure.sql_setup_candidates import SQLSetupCandidateRepository
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository


@dataclass(frozen=True, slots=True)
class WebhookIngestionServices:
    webhook_ingestion_service: WebhookIngestionService
    webhook_event_repository: WebhookEventRepository
    setup_candidate_repository: SetupCandidateRepository
    outcome_repository: OutcomeRepository
    backtest_repository: BacktestRepository
    journal_repository: JournalRepository


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
        webhook_event_repository: WebhookEventRepository = SQLWebhookEventRepository(engine)
        setup_candidate_repository: SetupCandidateRepository = SQLSetupCandidateRepository(engine)
        return WebhookIngestionServices(
            webhook_ingestion_service=WebhookIngestionService(
                webhook_event_repository,
                audit_logger,
                setup_candidate_repository=setup_candidate_repository,
            ),
            webhook_event_repository=webhook_event_repository,
            setup_candidate_repository=setup_candidate_repository,
            outcome_repository=SQLOutcomeRepository(engine),
            backtest_repository=SQLBacktestRepository(engine),
            journal_repository=SQLJournalRepository(engine),
        )

    webhook_event_repository = InMemoryWebhookEventRepository()
    setup_candidate_repository = InMemorySetupCandidateRepository()
    outcome_repository = InMemoryOutcomeRepository()
    return WebhookIngestionServices(
        webhook_ingestion_service=WebhookIngestionService(
            webhook_event_repository,
            audit_logger,
            setup_candidate_repository=setup_candidate_repository,
        ),
        webhook_event_repository=webhook_event_repository,
        setup_candidate_repository=setup_candidate_repository,
        outcome_repository=outcome_repository,
        backtest_repository=InMemoryBacktestRepository(outcome_repository),
        journal_repository=InMemoryJournalRepository(),
    )
