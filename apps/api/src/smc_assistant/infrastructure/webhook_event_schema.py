from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    MetaData,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

webhook_events = Table(
    "webhook_events",
    metadata,
    Column("event_id", String(length=200), primary_key=True),
    Column("event_type", String(length=80), nullable=False),
    Column("source", String(length=80), nullable=False),
    Column("schema_version", String(length=40), nullable=False),
    Column("payload", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("received_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("event_id"),
)

Index("ix_webhook_events_received_at", webhook_events.c.received_at)
