from sqlalchemy import Engine, create_engine

from smc_assistant.infrastructure.webhook_event_schema import metadata


def create_database_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def initialize_database_schema(engine: Engine) -> None:
    metadata.create_all(engine)
