from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str = "postgresql+psycopg://smc_assistant:change-me-local-only@localhost:5432/smc_assistant"
    webhook_event_repository: Literal["memory", "postgres"] = "memory"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
