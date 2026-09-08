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
    paper_max_risk_per_trade_percent: float = Field(default=1.0, gt=0, le=100)
    paper_max_daily_loss_r: float = Field(default=3.0, gt=0)
    paper_max_consecutive_losses: int = Field(default=3, ge=1)
    paper_minimum_risk_reward: float = Field(default=2.0, gt=0)
    paper_max_open_positions: int = Field(default=3, ge=1)
    paper_cooldown_minutes: int = Field(default=15, ge=0)
    paper_setup_score_minimum: float = Field(default=70.0, gt=0, le=100)
    paper_allowed_sessions: list[str] = Field(
        default_factory=lambda: ["ASIA", "LONDON", "NEW_YORK"]
    )
    paper_correlation_groups: list[list[str]] = Field(default_factory=list)
    paper_max_correlated_positions: int = Field(default=1, ge=1)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
