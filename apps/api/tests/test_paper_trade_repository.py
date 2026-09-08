import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from smc_assistant.application.paper_trading import (
    PaperTradeAlreadyExistsError,
    PaperTradeRevisionConflictError,
)
from smc_assistant.application.setup_candidates import SetupCandidateRecord
from smc_assistant.application.webhook_ingestion import WebhookEventRecord
from smc_assistant.domain.paper_trading import (
    PaperTrade,
    PaperTradeEvent,
    PaperTradeEventType,
    PaperTradeStatus,
)
from smc_assistant.infrastructure.in_memory_paper_trades import (
    InMemoryPaperTradeRepository,
)
from smc_assistant.infrastructure.sql_paper_trades import SQLPaperTradeRepository
from smc_assistant.infrastructure.sql_setup_candidates import SQLSetupCandidateRepository
from smc_assistant.infrastructure.sql_webhook_events import SQLWebhookEventRepository
from smc_assistant.infrastructure.webhook_event_schema import metadata

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
BACKENDS = ["memory", "sqlite"]
if os.environ.get("TEST_POSTGRES_URL"):
    BACKENDS.append("postgres")


@pytest.fixture(params=BACKENDS)
def repository(request: pytest.FixtureRequest):
    if request.param == "memory":
        yield InMemoryPaperTradeRepository()
        return
    if request.param == "postgres":
        engine = create_engine(os.environ["TEST_POSTGRES_URL"])
        schema = f"test_paper_trades_{uuid4().hex}"
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        scoped_engine = engine.execution_options(schema_translate_map={None: schema})
    else:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        schema = None
        scoped_engine = engine
    metadata.create_all(scoped_engine)
    event_id = "BTCUSDT-1-paper-repository"
    SQLWebhookEventRepository(scoped_engine).save_if_absent(
        WebhookEventRecord(
            event_id=event_id,
            event_type="SETUP_CANDIDATE",
            source="TRADINGVIEW",
            schema_version="1.0",
            payload={"eventId": event_id},
            received_at=NOW,
        )
    )
    SQLSetupCandidateRepository(scoped_engine).save_if_absent(
        SetupCandidateRecord(
            setup_id=event_id,
            event_id=event_id,
            schema_version="1.0",
            strategy_version="smc-rce-v1",
            scoring_config_version="rule-score-v1",
            symbol="BTCUSDT",
            exchange="BINANCE",
            timeframe="1",
            direction="LONG",
            htf_bias="BULLISH",
            score=90,
            accepted=True,
            components=[],
            rejection_reasons=[],
            positive_reasons=[],
            negative_reasons=[],
            bar_close_time=NOW,
            received_at=NOW,
        )
    )
    try:
        yield SQLPaperTradeRepository(scoped_engine)
    finally:
        if schema is not None:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        engine.dispose()


def trade() -> PaperTrade:
    return PaperTrade(
        trade_id=uuid4(),
        setup_id="BTCUSDT-1-paper-repository",
        event_id="BTCUSDT-1-paper-repository",
        symbol="BTCUSDT",
        exchange="BINANCE",
        timeframe="1",
        direction="LONG",
        session="NEW_YORK",
        strategy_version="smc-rce-v1",
        status=PaperTradeStatus.PENDING,
        entry_price=100,
        stop_loss=95,
        take_profit=110,
        planned_risk_reward=2,
        account_balance=10_000,
        risk_percent=1,
        risk_amount=100,
        quantity=20,
        opened_at=None,
        closed_at=None,
        exit_price=None,
        exit_reason=None,
        realized_pnl=None,
        realized_r=None,
        risk_policy_version="paper-risk-v1",
        created_at=NOW,
        updated_at=NOW,
        revision=1,
    )


def event(record: PaperTrade, event_type: PaperTradeEventType) -> PaperTradeEvent:
    return PaperTradeEvent(
        trade_id=record.trade_id,
        sequence=record.revision,
        event_type=event_type,
        occurred_at=record.updated_at,
        details={"status": record.status.value},
    )


def test_repository_persists_trade_transitions_and_events(repository) -> None:
    original = trade()
    repository.create(original, event(original, PaperTradeEventType.CREATED))
    opened = replace(
        original,
        status=PaperTradeStatus.OPEN,
        opened_at=NOW + timedelta(minutes=1),
        updated_at=NOW + timedelta(minutes=1),
        revision=2,
    )

    repository.update(
        opened,
        event(opened, PaperTradeEventType.OPENED),
        expected_revision=1,
    )

    assert repository.get(original.trade_id) == opened
    assert repository.get_by_setup_id(original.setup_id) == opened
    assert repository.list_recent(status=PaperTradeStatus.OPEN) == [opened]
    assert repository.list_all() == [opened]
    assert [item.event_type for item in repository.list_events(original.trade_id)] == [
        PaperTradeEventType.CREATED,
        PaperTradeEventType.OPENED,
    ]


def test_repository_rejects_duplicate_setup_and_stale_revision(repository) -> None:
    original = trade()
    repository.create(original, event(original, PaperTradeEventType.CREATED))
    duplicate = replace(original, trade_id=uuid4())
    with pytest.raises(PaperTradeAlreadyExistsError):
        repository.create(duplicate, event(duplicate, PaperTradeEventType.CREATED))

    updated = replace(original, updated_at=NOW + timedelta(minutes=1))
    with pytest.raises(PaperTradeRevisionConflictError):
        repository.update(
            updated,
            event(updated, PaperTradeEventType.PRICE_OBSERVED),
            expected_revision=0,
        )
