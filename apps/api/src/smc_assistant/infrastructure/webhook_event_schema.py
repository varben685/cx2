from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    Uuid,
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

outcome_records = Table(
    "outcome_records",
    metadata,
    Column("outcome_id", Uuid, primary_key=True),
    Column("run_id", Uuid, nullable=False),
    Column("event_id", String(length=200), nullable=False),
    Column("symbol", String(length=40), nullable=False),
    Column("label", String(length=20), nullable=False),
    Column("evaluated_at", DateTime(timezone=True), nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    UniqueConstraint("run_id", "event_id"),
)

Index("ix_outcome_records_event_id", outcome_records.c.event_id)
Index("ix_outcome_records_evaluated_at", outcome_records.c.evaluated_at)

backtest_runs = Table(
    "backtest_runs",
    metadata,
    Column("run_id", Uuid, primary_key=True),
    Column("completed_at", DateTime(timezone=True), nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
)
Index("ix_backtest_runs_completed_at", backtest_runs.c.completed_at)

journal_entries = Table(
    "journal_entries",
    metadata,
    Column("journal_id", Uuid, primary_key=True),
    Column(
        "setup_id",
        String(length=200),
        ForeignKey("setup_candidates.setup_id"),
        nullable=False,
        unique=True,
    ),
    Column(
        "outcome_id",
        Uuid,
        ForeignKey("outcome_records.outcome_id"),
        nullable=True,
    ),
    Column("symbol", String(length=40), nullable=False),
    Column("execution_status", String(length=20), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
)

Index("ix_journal_entries_updated_at", journal_entries.c.updated_at)
Index(
    "ix_journal_entries_symbol_status",
    journal_entries.c.symbol,
    journal_entries.c.execution_status,
)

journal_entry_revisions = Table(
    "journal_entry_revisions",
    metadata,
    Column(
        "journal_id",
        Uuid,
        ForeignKey("journal_entries.journal_id"),
        primary_key=True,
    ),
    Column("revision", Integer, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
)

paper_trades = Table(
    "paper_trades",
    metadata,
    Column("trade_id", Uuid, primary_key=True),
    Column(
        "setup_id",
        String(length=200),
        ForeignKey("setup_candidates.setup_id"),
        nullable=False,
        unique=True,
    ),
    Column("symbol", String(length=40), nullable=False),
    Column("status", String(length=20), nullable=False),
    Column("opened_at", DateTime(timezone=True), nullable=True),
    Column("closed_at", DateTime(timezone=True), nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("revision", Integer, nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
)

Index("ix_paper_trades_updated_at", paper_trades.c.updated_at)
Index("ix_paper_trades_symbol_status", paper_trades.c.symbol, paper_trades.c.status)

paper_trade_events = Table(
    "paper_trade_events",
    metadata,
    Column(
        "trade_id",
        Uuid,
        ForeignKey("paper_trades.trade_id"),
        primary_key=True,
    ),
    Column("sequence", Integer, primary_key=True),
    Column("event_type", String(length=30), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("snapshot", JSON().with_variant(JSONB(), "postgresql"), nullable=False),
)

Index("ix_paper_trade_events_occurred_at", paper_trade_events.c.occurred_at)
