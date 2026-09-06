from dataclasses import dataclass
from datetime import UTC
from hashlib import sha256

from pydantic import TypeAdapter

from smc_assistant.application.market_data import MarketDataProvider, MarketDataQuery
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.candles import Candle
from smc_assistant.domain.outcomes import (
    OutcomeConfig,
    TradeOutcome,
    TradePlan,
    evaluate_triple_barrier_outcome,
)


@dataclass(frozen=True, slots=True)
class TradingViewOutcomeEvaluation:
    event_id: str
    symbol: str
    timeframe: str
    trade_plan: TradePlan
    outcome: TradeOutcome
    candles_loaded: int
    config: OutcomeConfig
    market_data_sha256: str


def trade_plan_from_tradingview_payload(payload: TradingViewWebhookPayload) -> TradePlan:
    return TradePlan(
        direction=payload.direction,
        entry_price=payload.execution.entry,
        stop_loss=payload.execution.stop_loss,
        take_profit=payload.execution.take_profit,
    )


def evaluate_tradingview_outcome(
    payload: TradingViewWebhookPayload,
    market_data_provider: MarketDataProvider,
    config: OutcomeConfig | None = None,
) -> TradingViewOutcomeEvaluation:
    outcome_config = config or OutcomeConfig()
    trade_plan = trade_plan_from_tradingview_payload(payload)
    future_candles = market_data_provider.load_candles(
        MarketDataQuery(
            symbol=payload.symbol,
            timeframe=payload.timeframe,
            start_time=payload.bar_close_time.astimezone(UTC),
        )
    )
    outcome = evaluate_triple_barrier_outcome(
        trade_plan,
        future_candles,
        outcome_config,
    )

    return TradingViewOutcomeEvaluation(
        event_id=payload.event_id,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        trade_plan=trade_plan,
        outcome=outcome,
        candles_loaded=len(future_candles),
        config=outcome_config,
        market_data_sha256=sha256(
            TypeAdapter(tuple[Candle, ...]).dump_json(tuple(future_candles))
        ).hexdigest(),
    )
