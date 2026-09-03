from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
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

setup_candidates = Table(
    "setup_candidates",
    metadata,
    Column("setup_id", String(length=200), primary_key=True),
    Column("event_id", String(length=200), ForeignKey("webhook_events.event_id"), nullable=False),
    Column("schema_version", String(length=40), nullable=False),
    Column("strategy_version", String(length=80), nullable=False),
    Column("scoring_config_version", String(length=80), nullable=False),
    Column("symbol", String(length=40), nullable=False),
    Column("exchange", String(length=40), nullable=False),
    Column("timeframe", String(length=20), nullable=False),
    Column("direction", String(length=20), nullable=False),
    Column("htf_bias", String(length=20), nullable=False),
    Column("score", Float, nullable=False),
    Column("accepted", Boolean, nullable=False),
    Column("components", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("rejection_reasons", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("positive_reasons", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("negative_reasons", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    Column("bar_close_time", DateTime(timezone=True), nullable=False),
    Column("received_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("event_id"),
)

Index("ix_setup_candidates_received_at", setup_candidates.c.received_at)
Index("ix_setup_candidates_score", setup_candidates.c.score)
Index(
    "ix_setup_candidates_symbol_timeframe",
    setup_candidates.c.symbol,
    setup_candidates.c.timeframe,
)
