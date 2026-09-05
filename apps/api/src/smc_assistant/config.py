from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://smc_assistant:change-me-local-only@localhost:5432/smc_assistant"
    webhook_event_repository: Literal["memory", "postgres"] = "memory"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: DEFAULT_CORS_ORIGINS.copy())

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
