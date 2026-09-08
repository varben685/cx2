from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from test_outcome_evaluation import valid_payload
from test_outcome_records import save_example

from smc_assistant.analytics.performance import analyze_performance
from smc_assistant.application.backtests import BacktestRun
from smc_assistant.application.journal import JournalEntry
from smc_assistant.application.performance_analytics import build_performance_report
from smc_assistant.contracts.backtests import BacktestRequest
from smc_assistant.domain.enums import TradeOutcomeLabel
from smc_assistant.domain.journal import JournalExecutionStatus
from smc_assistant.infrastructure.in_memory_journal import InMemoryJournalRepository
from smc_assistant.infrastructure.in_memory_outcomes import InMemoryOutcomeRepository


def _record(base, *, sequence: int, net_r: float, label: TradeOutcomeLabel):
    occurred_at = datetime(2026, 1, 1, 12, sequence, tzinfo=UTC)
    outcome = replace(
        base.evaluation.outcome,
        label=label,
        net_realized_r=net_r,
        exit_time=occurred_at,
    )
    return replace(
        base,
        outcome_id=UUID(int=sequence),
        bar_close_time=occurred_at - timedelta(minutes=1),
        evaluation=replace(
            base.evaluation,
            event_id=f"analytics-event-{sequence}",
            outcome=outcome,
        ),
    )


def _journal(setup_id: str, status: JournalExecutionStatus) -> JournalEntry:
    timestamp = datetime(2026, 1, 1, 13, tzinfo=UTC)
    return JournalEntry(
        journal_id=uuid4(),
        setup_id=setup_id,
        outcome_id=None,
        event_id=setup_id,
        symbol="BTCUSDT",
        exchange="BINANCE",
        timeframe="1",
        direction="LONG",
        session="LONDON",
        strategy_version="smc-rce-v1",
        signal_time=timestamp,
        setup_snapshot={},
        outcome_snapshot=None,
        outcome_label=None,
        realized_r=None,
        mfe_r=None,
        mae_r=None,
        execution_status=status,
        user_note=None,
        screenshot_reference=None,
        manual_rating=None,
        manual_override=False,
        override_reason=None,
        tags=(),
        revision=1,
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_performance_curve_drawdown_averages_and_streaks_are_time_ordered() -> None:
    base = save_example(InMemoryOutcomeRepository()).record
    records = [
        _record(base, sequence=4, net_r=1, label=TradeOutcomeLabel.WIN),
        _record(base, sequence=2, net_r=-1, label=TradeOutcomeLabel.LOSS),
        _record(base, sequence=1, net_r=2, label=TradeOutcomeLabel.WIN),
        _record(base, sequence=3, net_r=-2, label=TradeOutcomeLabel.LOSS),
    ]

    analysis = analyze_performance(records)

    assert [point.net_r for point in analysis.equity_curve] == [2, -1, -2, 1]
    assert [point.cumulative_net_r for point in analysis.equity_curve] == [2, 1, -1, 0]
    assert [point.drawdown_r for point in analysis.equity_curve] == [0, 1, 3, 2]
    assert analysis.risk.average_win_r == 1.5
    assert analysis.risk.average_loss_r == -1.5
    assert analysis.risk.maximum_drawdown_r == 3
    assert analysis.risk.longest_winning_streak == 1
    assert analysis.risk.longest_losing_streak == 2


def test_report_groups_scores_components_and_journal_decisions() -> None:
    run_id = uuid4()
    first = valid_payload().model_dump(mode="json", by_alias=True)
    first["eventId"] = "analytics-event-1"
    first["features"]["session"] = "LONDON"
    second = valid_payload().model_dump(mode="json", by_alias=True)
    second["eventId"] = "analytics-event-2"
    second["features"].update(session="ASIA", displacementScore=0)
    second["marketStructure"].update(choch=False, liquiditySweep=False)
    request = BacktestRequest.model_validate(
        {"runId": str(run_id), "setups": [first, second], "candlesCsv": "data"}
    )
    base = save_example(InMemoryOutcomeRepository(), run_id=run_id).record
    outcomes = (
        _record(base, sequence=1, net_r=2, label=TradeOutcomeLabel.WIN),
        _record(base, sequence=2, net_r=-1, label=TradeOutcomeLabel.LOSS),
    )
    outcomes = tuple(replace(record, run_id=run_id) for record in outcomes)
    run = BacktestRun(
        run_id=run_id,
        request_sha256="a" * 64,
        started_at=datetime(2026, 1, 1, 11, tzinfo=UTC),
        completed_at=datetime(2026, 1, 1, 13, tzinfo=UTC),
        request=request,
        outcomes=outcomes,
    )
    journals = InMemoryJournalRepository()
    journals.create(_journal("analytics-event-1", JournalExecutionStatus.TAKEN))
    journals.create(_journal("analytics-event-2", JournalExecutionStatus.SKIPPED))

    report = build_performance_report(run, journals)

    assert report.statistics.total_net_r == 1
    assert {group.label for group in report.by_session} == {"ASIA", "LONDON"}
    assert {group.label for group in report.by_score_bucket} == {"0-49", "85-100"}
    assert len(report.by_instrument) == 1
    assert {group.label for group in report.by_direction} == {"LONG"}
    assert any(
        group.component.value == "CHOCH" and group.state.value == "ZERO"
        for group in report.by_setup_component
    )
    assert report.decisions.journaled_setups == 2
    assert report.decisions.followed_recommendation == 2
    assert report.decisions.agreement_rate == 1
    assert report.decisions.taken_statistics.total_net_r == 2
    assert report.decisions.skipped_statistics.total_net_r == -1
