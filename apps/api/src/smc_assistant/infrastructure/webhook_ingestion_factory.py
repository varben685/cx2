from dataclasses import dataclass

from smc_assistant.application.audit import AuditLogger
from smc_assistant.application.backtests import BacktestRepository
from smc_assistant.application.journal import JournalRepository
from smc_assistant.application.outcome_records import OutcomeRepository
from smc_assistant.application.paper_trading import PaperTradeRepository, PaperTradingService
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.tradingview_live import TradingViewLiveService
from smc_assistant.application.webhook_ingestion import (
    WebhookEventRepository,
    WebhookIngestionService,
)
from smc_assistant.config import Settings
from smc_assistant.domain.risk_policy import RiskPolicyConfig
from smc_assistant.infrastructure.database import (
    create_database_engine,
    initialize_database_schema,
)
from smc_assistant.infrastructure.in_memory_backtests import InMemoryBacktestRepository
from smc_assistant.infrastructure.in_memory_journal import InMemoryJournalRepository
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository
from smc_assistant.infrastructure.in_memory_paper_trades import InMemoryPaperTradeRepository
from smc_assistant.infrastructure.in_memory_setup_candidates import (
    InMemorySetupCandidateRepository,
)
from smc_assistant.infrastructure.in_memory_webhook_events import (
    InMemoryWebhookEventRepository,
)
from smc_assistant.infrastructure.sql_backtests import SQLBacktestRepository
from smc_assistant.infrastructure.sql_journal import SQLJournalRepository
from smc_assistant.infrastructure.sql_outcomes import SQLOutcomeRepository
from smc_assistant.infrastructure.sql_paper_trades import SQLPaperTradeRepository
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
    paper_trade_repository: PaperTradeRepository
    paper_trading_service: PaperTradingService
    tradingview_live_service: TradingViewLiveService


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
    risk_config = _risk_policy_config(settings)
    if settings.webhook_event_repository == "postgres":
        engine = create_database_engine(settings.database_url)
        initialize_database_schema(engine)
        webhook_event_repository: WebhookEventRepository = SQLWebhookEventRepository(engine)
        setup_candidate_repository: SetupCandidateRepository = SQLSetupCandidateRepository(engine)
        paper_trade_repository: PaperTradeRepository = SQLPaperTradeRepository(engine)
        webhook_ingestion_service = WebhookIngestionService(
            webhook_event_repository,
            audit_logger,
            setup_candidate_repository=setup_candidate_repository,
        )
        paper_trading_service = PaperTradingService(
            setup_candidate_repository,
            webhook_event_repository,
            paper_trade_repository,
            risk_config,
            audit_logger,
        )
        return WebhookIngestionServices(
            webhook_ingestion_service=webhook_ingestion_service,
            webhook_event_repository=webhook_event_repository,
            setup_candidate_repository=setup_candidate_repository,
            outcome_repository=SQLOutcomeRepository(engine),
            backtest_repository=SQLBacktestRepository(engine),
            journal_repository=SQLJournalRepository(engine),
            paper_trade_repository=paper_trade_repository,
            paper_trading_service=paper_trading_service,
            tradingview_live_service=TradingViewLiveService(
                webhook_ingestion_service,
                webhook_event_repository,
                paper_trading_service,
                auto_trade_enabled=settings.paper_auto_trade_enabled,
                account_balance=settings.paper_account_balance,
                risk_percent=settings.paper_default_risk_percent,
                audit_logger=audit_logger,
            ),
        )

    webhook_event_repository = InMemoryWebhookEventRepository()
    setup_candidate_repository = InMemorySetupCandidateRepository()
    outcome_repository = InMemoryOutcomeRepository()
    paper_trade_repository = InMemoryPaperTradeRepository()
    webhook_ingestion_service = WebhookIngestionService(
        webhook_event_repository,
        audit_logger,
        setup_candidate_repository=setup_candidate_repository,
    )
    paper_trading_service = PaperTradingService(
        setup_candidate_repository,
        webhook_event_repository,
        paper_trade_repository,
        risk_config,
        audit_logger,
    )
    return WebhookIngestionServices(
        webhook_ingestion_service=webhook_ingestion_service,
        webhook_event_repository=webhook_event_repository,
        setup_candidate_repository=setup_candidate_repository,
        outcome_repository=outcome_repository,
        backtest_repository=InMemoryBacktestRepository(outcome_repository),
        journal_repository=InMemoryJournalRepository(),
        paper_trade_repository=paper_trade_repository,
        paper_trading_service=paper_trading_service,
        tradingview_live_service=TradingViewLiveService(
            webhook_ingestion_service,
            webhook_event_repository,
            paper_trading_service,
            auto_trade_enabled=settings.paper_auto_trade_enabled,
            account_balance=settings.paper_account_balance,
            risk_percent=settings.paper_default_risk_percent,
            audit_logger=audit_logger,
        ),
    )


def _risk_policy_config(settings: Settings) -> RiskPolicyConfig:
    return RiskPolicyConfig(
        max_risk_per_trade_percent=settings.paper_max_risk_per_trade_percent,
        max_daily_loss_r=settings.paper_max_daily_loss_r,
        max_consecutive_losses=settings.paper_max_consecutive_losses,
        minimum_risk_reward=settings.paper_minimum_risk_reward,
        max_open_positions=settings.paper_max_open_positions,
        cooldown_minutes=settings.paper_cooldown_minutes,
        setup_score_minimum=settings.paper_setup_score_minimum,
        allowed_sessions=tuple(session.upper() for session in settings.paper_allowed_sessions),
        correlation_groups=tuple(
            tuple(symbol.upper() for symbol in group)
            for group in settings.paper_correlation_groups
        ),
        max_correlated_positions=settings.paper_max_correlated_positions,
    )
