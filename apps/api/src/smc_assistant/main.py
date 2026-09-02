from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from smc_assistant.api.errors import validation_exception_handler
from smc_assistant.api.health import router as health_router
from smc_assistant.api.webhooks import router as webhooks_router
from smc_assistant.config import Settings


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
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.include_router(health_router)
    app.include_router(webhooks_router)
    return app


app = create_app()
