from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from smc_assistant.api.analytics import router as analytics_router
from smc_assistant.api.backtests import router as backtests_router
from smc_assistant.api.errors import validation_exception_handler
from smc_assistant.api.health import router as health_router
from smc_assistant.api.journal import router as journal_router
from smc_assistant.api.outcomes import router as outcomes_router
from smc_assistant.api.paper_trades import router as paper_trades_router
from smc_assistant.api.setups import router as setups_router
from smc_assistant.api.webhooks import router as webhooks_router
from smc_assistant.config import Settings
from smc_assistant.infrastructure.logging_audit import create_audit_logger
from smc_assistant.infrastructure.webhook_ingestion_factory import (
    create_webhook_ingestion_services,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    app = FastAPI(
        title="SMC AI Trading Assistant API",
        version="0.1.0",
        summary="Webhook, setup analysis, journal and backtest API.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = app_settings
    app.state.audit_logger = create_audit_logger()
    webhook_ingestion_services = create_webhook_ingestion_services(
        app_settings,
        app.state.audit_logger,
    )
    app.state.webhook_ingestion_service = (
        webhook_ingestion_services.webhook_ingestion_service
    )
    app.state.webhook_event_repository = (
        webhook_ingestion_services.webhook_event_repository
    )
    app.state.setup_candidate_repository = (
        webhook_ingestion_services.setup_candidate_repository
    )
    app.state.outcome_repository = webhook_ingestion_services.outcome_repository
    app.state.backtest_repository = webhook_ingestion_services.backtest_repository
    app.state.journal_repository = webhook_ingestion_services.journal_repository
    app.state.paper_trade_repository = webhook_ingestion_services.paper_trade_repository
    app.state.paper_trading_service = webhook_ingestion_services.paper_trading_service
    app.state.paper_trade_outcome_service = (
        webhook_ingestion_services.paper_trade_outcome_service
    )
    app.state.tradingview_live_service = webhook_ingestion_services.tradingview_live_service
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health_router)
    app.include_router(webhooks_router)
    app.include_router(setups_router)
    app.include_router(analytics_router)
    app.include_router(backtests_router)
    app.include_router(outcomes_router)
    app.include_router(journal_router)
    app.include_router(paper_trades_router)
    return app


app = create_app()
