import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema
from test_outcome_evaluation import CapturingMarketDataProvider, make_candle, valid_payload

from smc_assistant.application.outcome_records import (
    IncompleteOutcomeError,
    OutcomeRecord,
    evaluate_and_save_tradingview_outcome,
)
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.outcomes import (
    OutcomeConfig,
    TradePlan,
    evaluate_triple_barrier_outcome,
)
from smc_assistant.infrastructure.database import initialize_database_schema
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository
from smc_assistant.infrastructure.sql_outcomes import SQLOutcomeRepository

BACKENDS = ["memory", "sqlite"]
if os.environ.get("TEST_POSTGRES_URL"):
    BACKENDS.append("postgres")


@pytest.fixture(params=BACKENDS)
def repository(request):
    if request.param == "memory":
        yield InMemoryOutcomeRepository()
        return

    if request.param == "postgres":
        engine = create_engine(os.environ["TEST_POSTGRES_URL"])
        schema = f"test_outcomes_{uuid4().hex}"
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        scoped_engine = engine.execution_options(schema_translate_map={None: schema})
        try:
            initialize_database_schema(scoped_engine)
            yield SQLOutcomeRepository(scoped_engine)
        finally:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
            engine.dispose()
    else:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        try:
            initialize_database_schema(engine)
            yield SQLOutcomeRepository(engine)
        finally:
            engine.dispose()


def save_example(repository, *, run_id=None, config=None):
    return evaluate_and_save_tradingview_outcome(
        valid_payload(),
        CapturingMarketDataProvider((make_candle(0), make_candle(1, high=111.0))),
        repository,
        run_id=run_id or uuid4(),
        config=config or OutcomeConfig(commission_bps_per_side=10, slippage_bps_per_side=5),
    )


def test_round_trip_preserves_complete_result_and_provenance(repository):
    saved = save_example(repository)
    loaded = repository.get_by_outcome_id(saved.record.outcome_id)

    assert saved.created is True
    assert loaded == saved.record
    assert loaded.evaluation.outcome.net_realized_r == 1.937
    assert loaded.evaluation.outcome.excursion.mfe_r == 2.2
    assert loaded.evaluation.outcome.excursion.mae_r == -0.2
    assert loaded.evaluation.config.commission_bps_per_side == 10
    assert loaded.evaluation.trade_plan.entry_price == 100
    assert loaded.evaluation.candles_loaded == 2
    assert len(loaded.evaluation.market_data_sha256) == 64
    assert loaded.strategy_version == "smc-rce-v1"
    assert loaded.engine_version == "triple-barrier-v1"
    assert loaded.evaluated_at.utcoffset() == timedelta(0)
    assert repository.get_by_run_event(loaded.run_id, loaded.evaluation.event_id) == loaded


def test_duplicate_keeps_first_snapshot_and_timestamp(repository):
    first = save_example(repository).record
    replacement = replace(
        first,
        outcome_id=uuid4(),
        evaluated_at=first.evaluated_at + timedelta(minutes=1),
        evaluation=replace(first.evaluation, config=OutcomeConfig()),
    )
    result = repository.save_if_absent(replacement)

    assert result.created is False
    assert result.record == first
    assert repository.get_by_outcome_id(replacement.outcome_id) is None
    assert repository.list_recent() == [first]


def test_retry_does_not_reload_market_data(repository):
    first = save_example(repository).record
    provider = CapturingMarketDataProvider(())
    result = evaluate_and_save_tradingview_outcome(
        valid_payload(), provider, repository, run_id=first.run_id, config=OutcomeConfig()
    )

    assert result.record == first
    assert result.created is False
    assert provider.query is None


def test_new_run_keeps_both_configurations(repository):
    first = save_example(repository).record
    second = save_example(repository, config=OutcomeConfig()).record

    assert second.run_id != first.run_id
    assert second.evaluation.outcome.net_realized_r == 2
    assert first.evaluation.outcome.net_realized_r == 1.937
    assert repository.list_recent(run_id=first.run_id) == [first]
    assert len(repository.list_recent(event_id=first.evaluation.event_id)) == 2


@pytest.mark.parametrize("candles", [(), (make_candle(0),)])
def test_incomplete_history_is_not_persisted_and_can_be_retried(repository, candles):
    run_id = uuid4()
    with pytest.raises(IncompleteOutcomeError, match="Not enough candles"):
        evaluate_and_save_tradingview_outcome(
            valid_payload(), CapturingMarketDataProvider(candles), repository, run_id=run_id
        )
    assert repository.list_recent() == []
    assert save_example(repository, run_id=run_id).created is True


def test_complete_timeout_can_be_persisted(repository):
    result = evaluate_and_save_tradingview_outcome(
        valid_payload(),
        CapturingMarketDataProvider((make_candle(0),)),
        repository,
        run_id=uuid4(),
        config=OutcomeConfig(max_holding_bars=1),
    )
    assert result.created is True
    assert result.record.evaluation.outcome.label == TradeOutcomeLabel.TIMEOUT


def test_complete_untriggered_window_can_be_persisted(repository):
    payload = valid_payload()
    payload.execution.entry = 200
    payload.execution.stop_loss = 195
    payload.execution.take_profit = 210
    result = evaluate_and_save_tradingview_outcome(
        payload,
        CapturingMarketDataProvider((make_candle(0),)),
        repository,
        run_id=uuid4(),
        config=OutcomeConfig(entry_timeout_bars=1),
    )
    assert result.created is True
    assert result.record.evaluation.outcome.label == TradeOutcomeLabel.NOT_TRIGGERED


@pytest.mark.parametrize("scenario", ["not_triggered", "timeout", "short_loss"])
def test_nullable_and_short_outcomes_round_trip(repository, scenario):
    base = save_example(repository).record
    plan = TradePlan(TradeDirection.LONG, 100, 95, 110)
    candles = (make_candle(0),)
    config = OutcomeConfig(max_holding_bars=1, entry_timeout_bars=1)
    if scenario == "not_triggered":
        plan = TradePlan(TradeDirection.LONG, 200, 195, 210)
    elif scenario == "short_loss":
        plan = TradePlan(TradeDirection.SHORT, 100, 105, 90)
        candles = (make_candle(0, high=106),)
    outcome = evaluate_triple_barrier_outcome(plan, candles, config)
    record = replace(
        base,
        outcome_id=uuid4(),
        run_id=uuid4(),
        evaluation=replace(base.evaluation, trade_plan=plan, outcome=outcome, config=config),
    )
    repository.save_if_absent(record)

    loaded = repository.get_by_outcome_id(record.outcome_id)
    assert loaded == record
    if scenario == "not_triggered":
        assert loaded.evaluation.outcome.label == TradeOutcomeLabel.NOT_TRIGGERED
        assert loaded.evaluation.outcome.excursion is None
        assert loaded.evaluation.outcome.costs is None
        assert loaded.evaluation.outcome.entry_time is None
    elif scenario == "timeout":
        assert loaded.evaluation.outcome.label == TradeOutcomeLabel.TIMEOUT
    else:
        assert loaded.evaluation.outcome.label == TradeOutcomeLabel.LOSS


def test_filters_and_limit_have_deterministic_order(repository):
    base = save_example(repository).record
    other = replace(
        base,
        outcome_id=UUID(int=1),
        run_id=uuid4(),
        evaluated_at=base.evaluated_at + timedelta(seconds=1),
        evaluation=replace(base.evaluation, event_id="ETH-event", symbol="ETHUSDT"),
    )
    tied = replace(other, outcome_id=UUID(int=2), run_id=uuid4())
    repository.save_if_absent(other)
    repository.save_if_absent(tied)

    assert repository.list_recent(limit=2) == [tied, other]
    assert repository.list_recent(symbol="BTCUSDT") == [base]
    assert repository.list_recent(run_id=other.run_id, symbol="ETHUSDT") == [other]
    assert repository.list_recent(run_id=other.run_id, event_id=base.evaluation.event_id) == []
    assert repository.get_by_outcome_id(uuid4()) is None
    assert repository.get_by_run_event(uuid4(), base.evaluation.event_id) is None
    with pytest.raises(ValueError, match="limit"):
        repository.list_recent(limit=0)


def test_primary_key_collision_is_not_treated_as_retry(repository):
    first = save_example(repository).record
    with pytest.raises((ValueError, IntegrityError)):
        repository.save_if_absent(replace(first, run_id=uuid4()))
    assert repository.list_recent() == [first]


def test_sql_duplicate_insert_race_returns_winner(tmp_path):
    engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'outcomes.db'}")
    initialize_database_schema(engine)
    repository = SQLOutcomeRepository(engine)
    first = save_example(repository).record

    class RacingRepository(SQLOutcomeRepository):
        calls = 0

        def get_by_run_event(self, run_id: UUID, event_id: str) -> OutcomeRecord | None:
            self.calls += 1
            if self.calls == 1:
                return None
            return super().get_by_run_event(run_id, event_id)

    try:
        result = RacingRepository(engine).save_if_absent(replace(first, outcome_id=uuid4()))
        assert result.record == first
        assert result.created is False
    finally:
        engine.dispose()

    reopened_engine = create_engine(f"sqlite+pysqlite:///{tmp_path / 'outcomes.db'}")
    try:
        initialize_database_schema(reopened_engine)
        assert SQLOutcomeRepository(reopened_engine).get_by_outcome_id(first.outcome_id) == first
    finally:
        reopened_engine.dispose()


def test_rejects_naive_record_timestamp():
    record = save_example(InMemoryOutcomeRepository()).record
    with pytest.raises(ValueError, match="timezone-aware"):
        replace(record, evaluated_at=datetime(2026, 1, 1))
    assert record.bar_close_time == datetime(2026, 1, 1, 12, 1, tzinfo=UTC)
