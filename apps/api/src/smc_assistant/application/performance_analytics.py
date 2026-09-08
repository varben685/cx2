from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from smc_assistant.analytics.backtest import BacktestStatistics, summarize_outcomes
from smc_assistant.analytics.performance import EquityPoint, RiskStatistics, analyze_performance
from smc_assistant.application.backtests import BacktestRun
from smc_assistant.application.journal import JournalRepository
from smc_assistant.application.outcome_records import OutcomeRecord
from smc_assistant.application.setup_scoring import score_tradingview_payload
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.journal import JournalExecutionStatus
from smc_assistant.domain.setup_scoring import ScoreComponentName, SetupScore, SetupScoringConfig


class ComponentScoreState(StrEnum):
    ZERO = "ZERO"
    PARTIAL = "PARTIAL"
    FULL = "FULL"


@dataclass(frozen=True, slots=True)
class AnalyticsBreakdown:
    key: str
    label: str
    statistics: BacktestStatistics


@dataclass(frozen=True, slots=True)
class ComponentBreakdown:
    component: ScoreComponentName
    state: ComponentScoreState
    statistics: BacktestStatistics


@dataclass(frozen=True, slots=True)
class DecisionComparison:
    journaled_setups: int
    taken: int
    skipped: int
    not_recorded: int
    followed_recommendation: int
    overrode_recommendation: int
    manual_overrides: int
    agreement_rate: float | None
    taken_statistics: BacktestStatistics
    skipped_statistics: BacktestStatistics


@dataclass(frozen=True, slots=True)
class BacktestPerformanceReport:
    run_id: UUID
    scoring_config_version: str
    statistics: BacktestStatistics
    risk: RiskStatistics
    equity_curve: tuple[EquityPoint, ...]
    by_session: tuple[AnalyticsBreakdown, ...]
    by_instrument: tuple[AnalyticsBreakdown, ...]
    by_direction: tuple[AnalyticsBreakdown, ...]
    by_score_bucket: tuple[AnalyticsBreakdown, ...]
    by_strategy_version: tuple[AnalyticsBreakdown, ...]
    by_setup_component: tuple[ComponentBreakdown, ...]
    decisions: DecisionComparison


@dataclass(frozen=True, slots=True)
class _ScoredOutcome:
    setup: TradingViewWebhookPayload
    outcome: OutcomeRecord
    score: SetupScore


def build_performance_report(
    run: BacktestRun,
    journal_repository: JournalRepository,
) -> BacktestPerformanceReport:
    config = SetupScoringConfig()
    outcomes_by_event = {
        record.evaluation.event_id: record for record in run.outcomes
    }
    items = tuple(
        _ScoredOutcome(
            setup=setup,
            outcome=outcomes_by_event[setup.event_id],
            score=score_tradingview_payload(setup, config),
        )
        for setup in run.request.setups
    )
    records = [item.outcome for item in items]
    performance = analyze_performance(records)
    return BacktestPerformanceReport(
        run_id=run.run_id,
        scoring_config_version=config.config_version,
        statistics=summarize_outcomes(record.evaluation.outcome for record in records),
        risk=performance.risk,
        equity_curve=performance.equity_curve,
        by_session=_group(items, lambda item: (item.setup.features.session.value,) * 2),
        by_instrument=_group(
            items,
            lambda item: (
                f"{item.setup.exchange}:{item.setup.symbol}",
                f"{item.setup.exchange} / {item.setup.symbol}",
            ),
        ),
        by_direction=_group(items, lambda item: (item.setup.direction.value,) * 2),
        by_score_bucket=_group(items, _score_bucket),
        by_strategy_version=_group(
            items,
            lambda item: (item.setup.strategy_version,) * 2,
        ),
        by_setup_component=_component_breakdowns(items),
        decisions=_decision_comparison(items, journal_repository),
    )


def _group(
    items: Iterable[_ScoredOutcome],
    key_for: Callable[[_ScoredOutcome], tuple[str, str]],
) -> tuple[AnalyticsBreakdown, ...]:
    groups: dict[tuple[str, str], list[OutcomeRecord]] = {}
    for item in items:
        groups.setdefault(key_for(item), []).append(item.outcome)
    return tuple(
        AnalyticsBreakdown(
            key=key,
            label=label,
            statistics=summarize_outcomes(
                record.evaluation.outcome for record in records
            ),
        )
        for (key, label), records in sorted(groups.items())
    )


def _score_bucket(item: _ScoredOutcome) -> tuple[str, str]:
    score = item.score.score
    if score < 50:
        return "00-49", "0-49"
    if score < 70:
        return "50-69", "50-69"
    if score < 85:
        return "70-84", "70-84"
    return "85-100", "85-100"


def _component_breakdowns(
    items: tuple[_ScoredOutcome, ...],
) -> tuple[ComponentBreakdown, ...]:
    groups: dict[tuple[ScoreComponentName, ComponentScoreState], list[OutcomeRecord]] = {}
    for item in items:
        for component in item.score.components:
            if component.score <= 0:
                state = ComponentScoreState.ZERO
            elif component.score >= component.max_score:
                state = ComponentScoreState.FULL
            else:
                state = ComponentScoreState.PARTIAL
            groups.setdefault((component.name, state), []).append(item.outcome)
    return tuple(
        ComponentBreakdown(
            component=component,
            state=state,
            statistics=summarize_outcomes(
                record.evaluation.outcome for record in records
            ),
        )
        for (component, state), records in sorted(
            groups.items(), key=lambda group: (group[0][0].value, group[0][1].value)
        )
    )


def _decision_comparison(
    items: tuple[_ScoredOutcome, ...],
    repository: JournalRepository,
) -> DecisionComparison:
    taken_records: list[OutcomeRecord] = []
    skipped_records: list[OutcomeRecord] = []
    journaled = taken = skipped = not_recorded = followed = overrode = manual = 0
    for item in items:
        journal = repository.get_by_setup_id(item.setup.event_id)
        if journal is None:
            continue
        journaled += 1
        manual += int(journal.manual_override)
        if journal.execution_status == JournalExecutionStatus.NOT_RECORDED:
            not_recorded += 1
            continue
        if journal.execution_status == JournalExecutionStatus.TAKEN:
            taken += 1
            taken_records.append(item.outcome)
            agrees = item.score.accepted
        else:
            skipped += 1
            skipped_records.append(item.outcome)
            agrees = not item.score.accepted
        followed += int(agrees)
        overrode += int(not agrees)
    compared = followed + overrode
    return DecisionComparison(
        journaled_setups=journaled,
        taken=taken,
        skipped=skipped,
        not_recorded=not_recorded,
        followed_recommendation=followed,
        overrode_recommendation=overrode,
        manual_overrides=manual,
        agreement_rate=round(followed / compared, 6) if compared else None,
        taken_statistics=summarize_outcomes(
            record.evaluation.outcome for record in taken_records
        ),
        skipped_statistics=summarize_outcomes(
            record.evaluation.outcome for record in skipped_records
        ),
    )
