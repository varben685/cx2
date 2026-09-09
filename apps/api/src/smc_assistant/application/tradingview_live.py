from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from smc_assistant.application.audit import (
    AuditEventType,
    AuditLogger,
    NoopAuditLogger,
    create_audit_event,
)
from smc_assistant.application.paper_trading import (
    PaperTradeAlreadyExistsError,
    PaperTradePriceBatch,
    PaperTradeRiskRejectedError,
    PaperTradingService,
)
from smc_assistant.application.webhook_ingestion import (
    WebhookEventConflictError,
    WebhookEventRecord,
    WebhookEventRepository,
    WebhookIngestionResult,
    WebhookIngestionService,
    WebhookIngestionStatus,
)
from smc_assistant.contracts.tradingview import (
    TradingViewMarketPricePayload,
    TradingViewWebhookPayload,
)
from smc_assistant.domain.paper_trading import PaperTrade


class PaperTradeAutomationStatus(StrEnum):
    CREATED = "CREATED"
    EXISTING = "EXISTING"
    DISABLED = "DISABLED"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    RISK_REJECTED = "RISK_REJECTED"


@dataclass(frozen=True, slots=True)
class PaperTradeAutomationResult:
    status: PaperTradeAutomationStatus
    trade: PaperTrade | None
    message: str


@dataclass(frozen=True, slots=True)
class LiveSetupWebhookResult:
    ingestion: WebhookIngestionResult
    automation: PaperTradeAutomationResult


@dataclass(frozen=True, slots=True)
class LiveMarketPriceWebhookResult:
    status: WebhookIngestionStatus
    event_id: str
    schema_version: str
    received_at: datetime
    first_received_at: datetime
    symbol: str
    exchange: str
    timeframe: str
    observed_at: datetime
    price: float
    batch: PaperTradePriceBatch | None
    message: str


class TradingViewLiveService:
    def __init__(
        self,
        ingestion_service: WebhookIngestionService,
        webhook_repository: WebhookEventRepository,
        paper_trading_service: PaperTradingService,
        *,
        auto_trade_enabled: bool,
        account_balance: float,
        risk_percent: float,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._ingestion = ingestion_service
        self._webhooks = webhook_repository
        self._paper_trading = paper_trading_service
        self._auto_trade_enabled = auto_trade_enabled
        self._account_balance = account_balance
        self._risk_percent = risk_percent
        self._audit_logger = audit_logger or NoopAuditLogger()

    def ingest_setup(
        self,
        payload: TradingViewWebhookPayload,
        *,
        received_at: datetime | None = None,
    ) -> LiveSetupWebhookResult:
        existing_record = self._webhooks.get_by_event_id(payload.event_id)
        if (
            existing_record is not None
            and existing_record.event_type != payload.event_type.value
        ):
            raise WebhookEventConflictError(
                "eventId already belongs to a different webhook event type."
            )
        ingestion = self._ingestion.ingest_tradingview(payload, received_at=received_at)
        if not self._auto_trade_enabled:
            automation = PaperTradeAutomationResult(
                status=PaperTradeAutomationStatus.DISABLED,
                trade=None,
                message="Automatic paper trading is disabled.",
            )
        elif ingestion.status == WebhookIngestionStatus.DUPLICATE:
            existing_trade = self._paper_trading.get_trade_by_setup(
                ingestion.setup_candidate_id
            )
            automation = PaperTradeAutomationResult(
                status=(
                    PaperTradeAutomationStatus.EXISTING
                    if existing_trade is not None
                    else PaperTradeAutomationStatus.NOT_ELIGIBLE
                ),
                trade=existing_trade,
                message=(
                    "The setup already has a paper trade."
                    if existing_trade is not None
                    else "A duplicate setup event cannot create a new paper trade."
                ),
            )
        elif not ingestion.setup_score.accepted:
            automation = PaperTradeAutomationResult(
                status=PaperTradeAutomationStatus.NOT_ELIGIBLE,
                trade=None,
                message="The setup score is not eligible for automatic paper trading.",
            )
        else:
            automation = self._create_or_get_trade(
                ingestion.setup_candidate_id,
                created_at=ingestion.first_received_at,
            )
        return LiveSetupWebhookResult(ingestion=ingestion, automation=automation)

    def ingest_market_price(
        self,
        payload: TradingViewMarketPricePayload,
        *,
        received_at: datetime | None = None,
    ) -> LiveMarketPriceWebhookResult:
        event_received_at = (received_at or datetime.now(UTC)).astimezone(UTC)
        record = WebhookEventRecord(
            event_id=payload.event_id,
            event_type=payload.event_type.value,
            source=payload.source.value,
            schema_version=payload.schema_version,
            payload=payload.model_dump(mode="json", by_alias=True),
            received_at=event_received_at,
        )
        save_result = self._webhooks.save_if_absent(record)
        if not save_result.created:
            if save_result.record.event_type != payload.event_type.value:
                raise WebhookEventConflictError(
                    "eventId already belongs to a different webhook event type."
                )
            existing = TradingViewMarketPricePayload.model_validate(save_result.record.payload)
            self._audit_logger.record(
                create_audit_event(
                    AuditEventType.WEBHOOK_DUPLICATE,
                    {
                        "event_id": existing.event_id,
                        "event_type": existing.event_type.value,
                        "source": existing.source.value,
                        "first_received_at": save_result.record.received_at.isoformat(),
                    },
                    occurred_at=event_received_at,
                )
            )
            return LiveMarketPriceWebhookResult(
                status=WebhookIngestionStatus.DUPLICATE,
                event_id=existing.event_id,
                schema_version=existing.schema_version,
                received_at=event_received_at,
                first_received_at=save_result.record.received_at,
                symbol=existing.symbol,
                exchange=existing.exchange,
                timeframe=existing.timeframe,
                observed_at=existing.observed_at,
                price=existing.price,
                batch=None,
                message="TradingView market price was already processed.",
            )

        batch = self._paper_trading.observe_market_price(
            symbol=payload.symbol,
            exchange=payload.exchange,
            timeframe=payload.timeframe,
            price=payload.price,
            occurred_at=payload.observed_at.astimezone(UTC),
        )
        self._audit_logger.record(
            create_audit_event(
                AuditEventType.WEBHOOK_ACCEPTED,
                {
                    "event_id": payload.event_id,
                    "event_type": payload.event_type.value,
                    "source": payload.source.value,
                    "symbol": payload.symbol,
                    "matched_trades": len(batch.matched_trade_ids),
                    "updated_trades": len(batch.updated_trades),
                    "ignored_trades": len(batch.ignored_trade_ids),
                },
                occurred_at=event_received_at,
            )
        )
        return LiveMarketPriceWebhookResult(
            status=WebhookIngestionStatus.ACCEPTED,
            event_id=payload.event_id,
            schema_version=payload.schema_version,
            received_at=event_received_at,
            first_received_at=event_received_at,
            symbol=payload.symbol,
            exchange=payload.exchange,
            timeframe=payload.timeframe,
            observed_at=payload.observed_at.astimezone(UTC),
            price=payload.price,
            batch=batch,
            message="TradingView market price processed.",
        )

    def _create_or_get_trade(
        self,
        setup_id: str,
        *,
        created_at: datetime,
    ) -> PaperTradeAutomationResult:
        try:
            creation = self._paper_trading.create_trade(
                setup_id,
                account_balance=self._account_balance,
                risk_percent=self._risk_percent,
                created_at=created_at,
            )
        except PaperTradeAlreadyExistsError:
            trade = self._paper_trading.get_trade_by_setup(setup_id)
            return PaperTradeAutomationResult(
                status=PaperTradeAutomationStatus.EXISTING,
                trade=trade,
                message="The setup already has a paper trade.",
            )
        except PaperTradeRiskRejectedError as error:
            reasons = ", ".join(reason.value for reason in error.decision.rejection_reasons)
            return PaperTradeAutomationResult(
                status=PaperTradeAutomationStatus.RISK_REJECTED,
                trade=None,
                message=f"Automatic paper trade rejected by risk policy: {reasons}.",
            )
        return PaperTradeAutomationResult(
            status=PaperTradeAutomationStatus.CREATED,
            trade=creation.trade,
            message="Automatic paper trade created.",
        )
