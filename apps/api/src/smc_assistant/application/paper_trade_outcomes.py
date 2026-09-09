import logging
from dataclasses import dataclass, replace
from datetime import UTC
from hashlib import sha256
from uuid import UUID, uuid4

from pydantic import TypeAdapter

from smc_assistant.application.audit import (
    AuditEventType,
    AuditLogger,
    NoopAuditLogger,
    create_audit_event,
)
from smc_assistant.application.journal import (
    JournalRepository,
    JournalRevisionConflictError,
)
from smc_assistant.application.notifications import (
    NoopNotificationAdapter,
    NotificationAdapter,
    PaperOutcomeNotification,
)
from smc_assistant.application.outcome_evaluation import TradingViewOutcomeEvaluation
from smc_assistant.application.outcome_records import (
    OutcomeRecord,
    OutcomeRepository,
    OutcomeSaveResult,
)
from smc_assistant.application.paper_trading import PaperTradeRepository
from smc_assistant.application.webhook_ingestion import WebhookEventRepository
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.outcomes import (
    OutcomeConfig,
    OutcomeExitReason,
    TradeCostEstimate,
    TradeExcursion,
    TradeOutcome,
    TradePlan,
)
from smc_assistant.domain.paper_trading import (
    PaperTrade,
    PaperTradeEvent,
    PaperTradeEventType,
    PaperTradeExitReason,
    PaperTradeStatus,
)

LIVE_PAPER_RUN_ID = UUID("00000000-0000-0000-0000-000000000007")
PAPER_OUTCOME_ENGINE_VERSION = "paper-execution-v1"
_event_adapter = TypeAdapter(tuple[PaperTradeEvent, ...])
_outcome_adapter = TypeAdapter(OutcomeRecord)
logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PaperOutcomeReconciliation:
    scanned: int
    created: int
    existing: int


class PaperTradeOutcomeService:
    def __init__(
        self,
        paper_trade_repository: PaperTradeRepository,
        webhook_repository: WebhookEventRepository,
        outcome_repository: OutcomeRepository,
        journal_repository: JournalRepository,
        notification_adapter: NotificationAdapter | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._trades = paper_trade_repository
        self._webhooks = webhook_repository
        self._outcomes = outcome_repository
        self._journals = journal_repository
        self._notifications = notification_adapter or NoopNotificationAdapter()
        self._audit_logger = audit_logger or NoopAuditLogger()

    def record_terminal_trade(self, trade: PaperTrade) -> OutcomeSaveResult | None:
        if trade.status not in {PaperTradeStatus.CLOSED, PaperTradeStatus.CANCELLED}:
            return None
        existing = self._outcomes.get_by_run_event(LIVE_PAPER_RUN_ID, trade.event_id)
        if existing is not None:
            self._attach_to_journal(trade, existing)
            return OutcomeSaveResult(record=existing, created=False)

        webhook = self._webhooks.get_by_event_id(trade.event_id)
        if webhook is None:
            raise ValueError("Paper trade source webhook event not found.")
        payload = TradingViewWebhookPayload.model_validate(webhook.payload)
        events = tuple(self._trades.list_events(trade.trade_id))
        record = _outcome_record_from_trade(trade, payload, events)
        saved = self._outcomes.save_if_absent(record)
        self._attach_to_journal(trade, saved.record)
        if saved.created:
            self._audit_logger.record(
                create_audit_event(
                    AuditEventType.PAPER_OUTCOME_RECORDED,
                    {
                        "outcome_id": str(saved.record.outcome_id),
                        "trade_id": str(trade.trade_id),
                        "setup_id": trade.setup_id,
                        "symbol": trade.symbol,
                        "label": saved.record.evaluation.outcome.label.value,
                    },
                    occurred_at=saved.record.evaluated_at,
                )
            )
            self._send_notification(trade, saved.record)
        return saved

    def reconcile(self) -> PaperOutcomeReconciliation:
        terminal = [
            trade
            for trade in self._trades.list_all()
            if trade.status in {PaperTradeStatus.CLOSED, PaperTradeStatus.CANCELLED}
        ]
        created = 0
        for trade in terminal:
            result = self.record_terminal_trade(trade)
            if result is not None and result.created:
                created += 1
        return PaperOutcomeReconciliation(
            scanned=len(terminal),
            created=created,
            existing=len(terminal) - created,
        )

    def _attach_to_journal(self, trade: PaperTrade, outcome: OutcomeRecord) -> None:
        journal = self._journals.get_by_setup_id(trade.setup_id)
        if journal is None or journal.outcome_id is not None:
            return
        result = outcome.evaluation.outcome
        excursion = result.excursion
        updated = replace(
            journal,
            outcome_id=outcome.outcome_id,
            outcome_snapshot=_outcome_adapter.dump_python(outcome, mode="json"),
            outcome_label=result.label.value,
            realized_r=result.net_realized_r,
            mfe_r=excursion.mfe_r if excursion is not None else None,
            mae_r=excursion.mae_r if excursion is not None else None,
            revision=journal.revision + 1,
            updated_at=max(journal.updated_at, outcome.evaluated_at),
        )
        try:
            self._journals.update(updated, expected_revision=journal.revision)
        except JournalRevisionConflictError:
            current = self._journals.get_by_setup_id(trade.setup_id)
            if current is None or current.outcome_id is not None:
                return
            self._journals.update(
                replace(
                    current,
                    outcome_id=outcome.outcome_id,
                    outcome_snapshot=updated.outcome_snapshot,
                    outcome_label=updated.outcome_label,
                    realized_r=updated.realized_r,
                    mfe_r=updated.mfe_r,
                    mae_r=updated.mae_r,
                    revision=current.revision + 1,
                    updated_at=max(current.updated_at, outcome.evaluated_at),
                ),
                expected_revision=current.revision,
            )

    def _send_notification(self, trade: PaperTrade, outcome: OutcomeRecord) -> None:
        if not self._notifications.enabled:
            return
        result = outcome.evaluation.outcome
        try:
            self._notifications.send_paper_outcome(
                PaperOutcomeNotification(
                    outcome_id=outcome.outcome_id,
                    trade_id=trade.trade_id,
                    setup_id=trade.setup_id,
                    symbol=trade.symbol,
                    label=result.label,
                    realized_r=result.net_realized_r,
                    occurred_at=outcome.evaluated_at,
                )
            )
        except Exception as error:
            logger.exception("paper_outcome_notification_failed")
            self._audit_logger.record(
                create_audit_event(
                    AuditEventType.PAPER_OUTCOME_NOTIFICATION_FAILED,
                    {
                        "outcome_id": str(outcome.outcome_id),
                        "trade_id": str(trade.trade_id),
                        "symbol": trade.symbol,
                        "error_type": type(error).__name__,
                    },
                    occurred_at=outcome.evaluated_at,
                )
            )
            return
        self._audit_logger.record(
            create_audit_event(
                AuditEventType.PAPER_OUTCOME_NOTIFICATION_SENT,
                {
                    "outcome_id": str(outcome.outcome_id),
                    "trade_id": str(trade.trade_id),
                    "symbol": trade.symbol,
                    "label": result.label.value,
                },
                occurred_at=outcome.evaluated_at,
            )
        )


def _outcome_record_from_trade(
    trade: PaperTrade,
    payload: TradingViewWebhookPayload,
    events: tuple[PaperTradeEvent, ...],
) -> OutcomeRecord:
    if trade.closed_at is None:
        raise ValueError("Terminal paper trade requires closed_at.")
    plan = TradePlan(
        direction=TradeDirection(trade.direction),
        entry_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
    )
    outcome = _trade_outcome(trade, events, plan)
    return OutcomeRecord(
        outcome_id=uuid4(),
        run_id=LIVE_PAPER_RUN_ID,
        schema_version=payload.schema_version,
        strategy_version=trade.strategy_version,
        engine_version=PAPER_OUTCOME_ENGINE_VERSION,
        exchange=trade.exchange,
        bar_close_time=payload.bar_close_time.astimezone(UTC),
        evaluated_at=trade.closed_at.astimezone(UTC),
        evaluation=TradingViewOutcomeEvaluation(
            event_id=trade.event_id,
            symbol=trade.symbol,
            timeframe=trade.timeframe,
            trade_plan=plan,
            outcome=outcome,
            candles_loaded=_market_observation_count(events),
            config=OutcomeConfig(),
            market_data_sha256=sha256(_event_adapter.dump_json(events)).hexdigest(),
        ),
    )


def _trade_outcome(
    trade: PaperTrade,
    events: tuple[PaperTradeEvent, ...],
    plan: TradePlan,
) -> TradeOutcome:
    if trade.status == PaperTradeStatus.CANCELLED:
        return TradeOutcome(
            label=TradeOutcomeLabel.CANCELLED,
            exit_reason=OutcomeExitReason.PAPER_TRADE_CANCELLED,
            realized_r=None,
            net_realized_r=None,
            costs=None,
            excursion=None,
            entry_time=None,
            exit_time=trade.closed_at,
            exit_price=None,
            bars_to_entry=None,
            bars_held=None,
        )
    if trade.realized_r is None or trade.exit_reason is None:
        raise ValueError("Closed paper trade requires realized outcome data.")
    label = _outcome_label(trade.exit_reason, trade.realized_r)
    return TradeOutcome(
        label=label,
        exit_reason=_outcome_exit_reason(trade.exit_reason),
        realized_r=trade.realized_r,
        net_realized_r=trade.realized_r,
        costs=TradeCostEstimate(0.0, 0.0, 0.0, 0.0),
        excursion=_close_price_excursion(events, plan, trade.exit_price),
        entry_time=trade.opened_at,
        exit_time=trade.closed_at,
        exit_price=trade.exit_price,
        bars_to_entry=_bars_to_entry(events),
        bars_held=_bars_held(events),
    )


def _outcome_label(
    reason: PaperTradeExitReason,
    realized_r: float,
) -> TradeOutcomeLabel:
    if reason == PaperTradeExitReason.TAKE_PROFIT:
        return TradeOutcomeLabel.WIN
    if reason == PaperTradeExitReason.STOP_LOSS:
        return TradeOutcomeLabel.LOSS
    if realized_r > 0:
        return TradeOutcomeLabel.WIN
    if realized_r < 0:
        return TradeOutcomeLabel.LOSS
    return TradeOutcomeLabel.BREAK_EVEN


def _outcome_exit_reason(reason: PaperTradeExitReason) -> OutcomeExitReason:
    if reason == PaperTradeExitReason.TAKE_PROFIT:
        return OutcomeExitReason.TAKE_PROFIT_HIT
    if reason == PaperTradeExitReason.STOP_LOSS:
        return OutcomeExitReason.STOP_LOSS_HIT
    return OutcomeExitReason.MANUAL_CLOSE


def _market_prices(events: tuple[PaperTradeEvent, ...]) -> list[tuple[int, float]]:
    prices: list[tuple[int, float]] = []
    for event in events:
        value = event.details.get("marketPrice")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            prices.append((event.sequence, float(value)))
    return prices


def _market_observation_count(events: tuple[PaperTradeEvent, ...]) -> int:
    return len(_market_prices(events))


def _bars_to_entry(events: tuple[PaperTradeEvent, ...]) -> int | None:
    opened = next(
        (event for event in events if event.event_type == PaperTradeEventType.OPENED),
        None,
    )
    if opened is None:
        return None
    return sum(sequence <= opened.sequence for sequence, _ in _market_prices(events))


def _bars_held(events: tuple[PaperTradeEvent, ...]) -> int | None:
    opened = next(
        (event for event in events if event.event_type == PaperTradeEventType.OPENED),
        None,
    )
    if opened is None:
        return None
    return sum(sequence >= opened.sequence for sequence, _ in _market_prices(events))


def _close_price_excursion(
    events: tuple[PaperTradeEvent, ...],
    plan: TradePlan,
    exit_price: float | None,
) -> TradeExcursion | None:
    opened = next(
        (event for event in events if event.event_type == PaperTradeEventType.OPENED),
        None,
    )
    if opened is None:
        return None
    prices = [
        price
        for sequence, price in _market_prices(events)
        if sequence >= opened.sequence
    ]
    if exit_price is not None:
        prices.append(exit_price)
    if not prices:
        return None
    if plan.direction == TradeDirection.LONG:
        favorable = max(prices)
        adverse = min(prices)
        mfe_r = (favorable - plan.entry_price) / plan.initial_risk
        mae_r = (adverse - plan.entry_price) / plan.initial_risk
    else:
        favorable = min(prices)
        adverse = max(prices)
        mfe_r = (plan.entry_price - favorable) / plan.initial_risk
        mae_r = (plan.entry_price - adverse) / plan.initial_risk
    return TradeExcursion(
        mfe_r=round(mfe_r, 4),
        mae_r=round(mae_r, 4),
        max_favorable_price=favorable,
        max_adverse_price=adverse,
    )
