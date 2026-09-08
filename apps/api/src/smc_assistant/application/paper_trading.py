from dataclasses import dataclass, replace
from datetime import UTC, datetime
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from smc_assistant.application.audit import (
    AuditEventType,
    AuditLogger,
    NoopAuditLogger,
    create_audit_event,
)
from smc_assistant.application.setup_candidates import SetupCandidateRepository
from smc_assistant.application.webhook_ingestion import WebhookEventRepository
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.paper_trading import (
    PaperTrade,
    PaperTradeEvent,
    PaperTradeEventType,
    PaperTradeExitReason,
    PaperTradeStatus,
)
from smc_assistant.domain.risk_policy import (
    ClosedTradeRisk,
    OpenPositionRisk,
    RiskPolicyConfig,
    RiskPolicyDecision,
    RiskPolicyInput,
    evaluate_risk_policy,
)


class PaperTradingError(ValueError):
    pass


class PaperTradeNotFoundError(PaperTradingError):
    pass


class PaperTradeSetupNotFoundError(PaperTradingError):
    pass


class PaperTradeAlreadyExistsError(PaperTradingError):
    pass


class PaperTradeRiskRejectedError(PaperTradingError):
    def __init__(self, decision: RiskPolicyDecision) -> None:
        self.decision = decision
        reasons = ", ".join(reason.value for reason in decision.rejection_reasons)
        super().__init__(f"Paper trade rejected by risk policy: {reasons}.")


class PaperTradeTransitionError(PaperTradingError):
    pass


class PaperTradeRevisionConflictError(PaperTradingError):
    pass


@dataclass(frozen=True, slots=True)
class PaperTradeCreation:
    trade: PaperTrade
    risk_decision: RiskPolicyDecision


class PaperTradeRepository(Protocol):
    def create(self, trade: PaperTrade, event: PaperTradeEvent) -> PaperTrade:
        pass

    def get(self, trade_id: UUID) -> PaperTrade | None:
        pass

    def get_by_setup_id(self, setup_id: str) -> PaperTrade | None:
        pass

    def list_recent(
        self,
        *,
        limit: int = 100,
        status: PaperTradeStatus | None = None,
        symbol: str | None = None,
    ) -> list[PaperTrade]:
        pass

    def list_all(self) -> list[PaperTrade]:
        pass

    def update(
        self,
        trade: PaperTrade,
        event: PaperTradeEvent,
        *,
        expected_revision: int,
    ) -> PaperTrade:
        pass

    def list_events(self, trade_id: UUID) -> list[PaperTradeEvent]:
        pass


class PaperTradingService:
    def __init__(
        self,
        setup_repository: SetupCandidateRepository,
        webhook_repository: WebhookEventRepository,
        paper_trade_repository: PaperTradeRepository,
        risk_config: RiskPolicyConfig | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._setups = setup_repository
        self._webhooks = webhook_repository
        self._trades = paper_trade_repository
        self._risk_config = risk_config or RiskPolicyConfig()
        self._audit_logger = audit_logger or NoopAuditLogger()
        self._creation_lock = Lock()

    def create_trade(
        self,
        setup_id: str,
        *,
        account_balance: float,
        risk_percent: float,
        created_at: datetime | None = None,
    ) -> PaperTradeCreation:
        with self._creation_lock:
            return self._create_trade(
                setup_id,
                account_balance=account_balance,
                risk_percent=risk_percent,
                created_at=created_at,
            )

    def _create_trade(
        self,
        setup_id: str,
        *,
        account_balance: float,
        risk_percent: float,
        created_at: datetime | None,
    ) -> PaperTradeCreation:
        if self._trades.get_by_setup_id(setup_id) is not None:
            raise PaperTradeAlreadyExistsError("A paper trade already exists for this setup.")
        setup = self._setups.get_by_setup_id(setup_id)
        if setup is None:
            raise PaperTradeSetupNotFoundError("Setup candidate not found.")
        webhook = self._webhooks.get_by_event_id(setup.event_id)
        if webhook is None:
            raise PaperTradeSetupNotFoundError("Source webhook event not found.")
        payload = TradingViewWebhookPayload.model_validate(webhook.payload)
        now = (created_at or datetime.now(UTC)).astimezone(UTC)
        existing = self._trades.list_all()
        open_positions = tuple(
            OpenPositionRisk(symbol=trade.symbol.upper())
            for trade in existing
            if trade.status in {PaperTradeStatus.PENDING, PaperTradeStatus.OPEN}
        )
        closed_trades = tuple(
            ClosedTradeRisk(
                symbol=trade.symbol.upper(),
                closed_at=trade.closed_at,
                realized_r=trade.realized_r,
            )
            for trade in existing
            if trade.status == PaperTradeStatus.CLOSED
            and trade.closed_at is not None
            and trade.realized_r is not None
        )
        decision = evaluate_risk_policy(
            RiskPolicyInput(
                setup_accepted=setup.accepted,
                setup_score=setup.score,
                risk_percent=risk_percent,
                planned_risk_reward=payload.execution.risk_reward,
                session=payload.features.session.value,
                symbol=setup.symbol.upper(),
                evaluated_at=now,
                open_positions=open_positions,
                closed_trades=closed_trades,
            ),
            self._risk_config,
        )
        if not decision.approved:
            self._audit_logger.record(
                create_audit_event(
                    AuditEventType.PAPER_TRADE_RISK_REJECTED,
                    {
                        "setup_id": setup.setup_id,
                        "symbol": setup.symbol,
                        "risk_percent": risk_percent,
                        "policy_version": decision.policy_version,
                        "rejection_reasons": ",".join(
                            reason.value for reason in decision.rejection_reasons
                        ),
                    },
                    occurred_at=now,
                )
            )
            raise PaperTradeRiskRejectedError(decision)

        risk_amount = account_balance * (risk_percent / 100)
        unit_risk = abs(payload.entry - payload.stop_loss)
        trade = PaperTrade(
            trade_id=uuid4(),
            setup_id=setup.setup_id,
            event_id=setup.event_id,
            symbol=setup.symbol,
            exchange=setup.exchange,
            timeframe=setup.timeframe,
            direction=setup.direction,
            session=payload.features.session.value,
            strategy_version=setup.strategy_version,
            status=PaperTradeStatus.PENDING,
            entry_price=payload.entry,
            stop_loss=payload.stop_loss,
            take_profit=payload.take_profit,
            planned_risk_reward=payload.execution.risk_reward,
            account_balance=account_balance,
            risk_percent=risk_percent,
            risk_amount=risk_amount,
            quantity=risk_amount / unit_risk,
            opened_at=None,
            closed_at=None,
            exit_price=None,
            exit_reason=None,
            realized_pnl=None,
            realized_r=None,
            risk_policy_version=decision.policy_version,
            created_at=now,
            updated_at=now,
            revision=1,
        )
        event = PaperTradeEvent(
            trade_id=trade.trade_id,
            sequence=1,
            event_type=PaperTradeEventType.CREATED,
            occurred_at=now,
            details={
                "entryPrice": trade.entry_price,
                "stopLoss": trade.stop_loss,
                "takeProfit": trade.take_profit,
                "riskAmount": trade.risk_amount,
                "quantity": trade.quantity,
            },
        )
        saved = self._trades.create(trade, event)
        self._audit_logger.record(
            create_audit_event(
                AuditEventType.PAPER_TRADE_CREATED,
                {
                    "trade_id": str(saved.trade_id),
                    "setup_id": saved.setup_id,
                    "symbol": saved.symbol,
                    "risk_percent": saved.risk_percent,
                    "policy_version": saved.risk_policy_version,
                },
                occurred_at=now,
            )
        )
        return PaperTradeCreation(trade=saved, risk_decision=decision)

    def observe_price(
        self,
        trade_id: UUID,
        *,
        price: float,
        occurred_at: datetime | None = None,
    ) -> PaperTrade:
        trade = self._require_trade(trade_id)
        if trade.status not in {PaperTradeStatus.PENDING, PaperTradeStatus.OPEN}:
            raise PaperTradeTransitionError("Only pending or open trades accept market prices.")
        now = self._transition_time(trade, occurred_at)
        if trade.status == PaperTradeStatus.PENDING and _entry_reached(trade, price):
            updated = replace(
                trade,
                status=PaperTradeStatus.OPEN,
                opened_at=now,
                updated_at=now,
                revision=trade.revision + 1,
            )
            event_type = PaperTradeEventType.OPENED
        elif trade.status == PaperTradeStatus.OPEN and (reason := _exit_reason(trade, price)):
            exit_price = (
                trade.stop_loss
                if reason == PaperTradeExitReason.STOP_LOSS
                else trade.take_profit
            )
            updated = _closed_trade(trade, exit_price=exit_price, reason=reason, closed_at=now)
            event_type = PaperTradeEventType.CLOSED
        else:
            updated = replace(
                trade,
                updated_at=now,
                revision=trade.revision + 1,
            )
            event_type = PaperTradeEventType.PRICE_OBSERVED
        event = PaperTradeEvent(
            trade_id=trade.trade_id,
            sequence=updated.revision,
            event_type=event_type,
            occurred_at=now,
            details=_price_event_details(updated, price),
        )
        return self._save_transition(trade, updated, event)

    def close_trade(
        self,
        trade_id: UUID,
        *,
        exit_price: float,
        closed_at: datetime | None = None,
    ) -> PaperTrade:
        trade = self._require_trade(trade_id)
        if trade.status != PaperTradeStatus.OPEN:
            raise PaperTradeTransitionError("Only open paper trades can be closed manually.")
        now = self._transition_time(trade, closed_at)
        updated = _closed_trade(
            trade,
            exit_price=exit_price,
            reason=PaperTradeExitReason.MANUAL,
            closed_at=now,
        )
        event = PaperTradeEvent(
            trade_id=trade.trade_id,
            sequence=updated.revision,
            event_type=PaperTradeEventType.CLOSED,
            occurred_at=now,
            details={"exitPrice": exit_price, "exitReason": PaperTradeExitReason.MANUAL.value},
        )
        return self._save_transition(trade, updated, event)

    def cancel_trade(
        self,
        trade_id: UUID,
        *,
        cancelled_at: datetime | None = None,
    ) -> PaperTrade:
        trade = self._require_trade(trade_id)
        if trade.status != PaperTradeStatus.PENDING:
            raise PaperTradeTransitionError("Only pending paper trades can be cancelled.")
        now = self._transition_time(trade, cancelled_at)
        updated = replace(
            trade,
            status=PaperTradeStatus.CANCELLED,
            closed_at=now,
            exit_reason=PaperTradeExitReason.CANCELLED,
            updated_at=now,
            revision=trade.revision + 1,
        )
        event = PaperTradeEvent(
            trade_id=trade.trade_id,
            sequence=updated.revision,
            event_type=PaperTradeEventType.CANCELLED,
            occurred_at=now,
            details={"status": updated.status.value},
        )
        return self._save_transition(trade, updated, event)

    def _require_trade(self, trade_id: UUID) -> PaperTrade:
        trade = self._trades.get(trade_id)
        if trade is None:
            raise PaperTradeNotFoundError("Paper trade not found.")
        return trade

    def _save_transition(
        self,
        previous: PaperTrade,
        updated: PaperTrade,
        event: PaperTradeEvent,
    ) -> PaperTrade:
        saved = self._trades.update(
            updated,
            event,
            expected_revision=previous.revision,
        )
        self._audit_logger.record(
            create_audit_event(
                AuditEventType.PAPER_TRADE_TRANSITIONED,
                {
                    "trade_id": str(saved.trade_id),
                    "symbol": saved.symbol,
                    "from_status": previous.status.value,
                    "to_status": saved.status.value,
                    "event_type": event.event_type.value,
                    "revision": saved.revision,
                },
                occurred_at=event.occurred_at,
            )
        )
        return saved

    @staticmethod
    def _transition_time(trade: PaperTrade, value: datetime | None) -> datetime:
        now = (value or datetime.now(UTC)).astimezone(UTC)
        if now < trade.updated_at:
            raise PaperTradeTransitionError("Transition time cannot precede the latest event.")
        return now


def _entry_reached(trade: PaperTrade, price: float) -> bool:
    return price <= trade.entry_price if trade.direction == "LONG" else price >= trade.entry_price


def _exit_reason(trade: PaperTrade, price: float) -> PaperTradeExitReason | None:
    if trade.direction == "LONG":
        if price <= trade.stop_loss:
            return PaperTradeExitReason.STOP_LOSS
        if price >= trade.take_profit:
            return PaperTradeExitReason.TAKE_PROFIT
    else:
        if price >= trade.stop_loss:
            return PaperTradeExitReason.STOP_LOSS
        if price <= trade.take_profit:
            return PaperTradeExitReason.TAKE_PROFIT
    return None


def _closed_trade(
    trade: PaperTrade,
    *,
    exit_price: float,
    reason: PaperTradeExitReason,
    closed_at: datetime,
) -> PaperTrade:
    price_change = (
        exit_price - trade.entry_price
        if trade.direction == "LONG"
        else trade.entry_price - exit_price
    )
    realized_pnl = price_change * trade.quantity
    return replace(
        trade,
        status=PaperTradeStatus.CLOSED,
        closed_at=closed_at,
        exit_price=exit_price,
        exit_reason=reason,
        realized_pnl=round(realized_pnl, 8),
        realized_r=round(realized_pnl / trade.risk_amount, 6),
        updated_at=closed_at,
        revision=trade.revision + 1,
    )


def _price_event_details(trade: PaperTrade, market_price: float) -> dict[str, object]:
    details: dict[str, object] = {
        "marketPrice": market_price,
        "status": trade.status.value,
    }
    if trade.status == PaperTradeStatus.OPEN:
        details["fillPrice"] = trade.entry_price
    if trade.status == PaperTradeStatus.CLOSED:
        details.update(
            exitPrice=trade.exit_price,
            exitReason=trade.exit_reason.value if trade.exit_reason is not None else None,
            realizedPnl=trade.realized_pnl,
            realizedR=trade.realized_r,
        )
    return details
