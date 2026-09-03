from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from smc_assistant.api.errors import validation_exception_handler
from smc_assistant.api.health import router as health_router
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
    app.state.setup_candidate_repository = (
        webhook_ingestion_services.setup_candidate_repository
    )
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health_router)
    app.include_router(webhooks_router)
    app.include_router(setups_router)
    return app


app = create_app()
