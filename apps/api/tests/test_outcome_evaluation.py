from datetime import UTC, datetime, timedelta

from smc_assistant.application.market_data import MarketDataProvider, MarketDataQuery
from smc_assistant.application.outcome_evaluation import (
    evaluate_tradingview_outcome,
    trade_plan_from_tradingview_payload,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.candles import Candle
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.outcomes import OutcomeConfig, OutcomeExitReason
from smc_assistant.infrastructure.csv_market_data import CsvMarketDataProvider


def valid_payload() -> TradingViewWebhookPayload:
    return TradingViewWebhookPayload.model_validate(
        {
            "schemaVersion": "1.0",
            "eventId": "BTCUSDT-1-1767225660000-LONG",
            "eventType": "SETUP_CANDIDATE",
            "source": "TRADINGVIEW",
            "strategyVersion": "smc-rce-v1",
            "symbol": "BTCUSDT",
            "exchange": "BINANCE",
            "timeframe": "1",
            "barOpenTime": "2026-01-01T12:00:00Z",
            "barCloseTime": "2026-01-01T12:01:00Z",
            "direction": "LONG",
            "marketStructure": {
                "htfTimeframe": "15",
                "htfBias": "BULLISH",
                "bos": True,
                "choch": True,
                "liquiditySweep": True,
            },
            "fvg": {
                "lower": 99.0,
                "upper": 101.0,
                "equilibrium": 100.0,
                "sizeAtrRatio": 0.42,
                "mitigationPercent": 0.0,
            },
            "execution": {
                "entry": 100.0,
                "stopLoss": 95.0,
                "takeProfit": 110.0,
                "riskReward": 2.0,
            },
            "features": {
                "atr": None,
                "relativeVolume": None,
                "displacementScore": 0.81,
                "session": "NEW_YORK",
            },
        }
    )


def make_candle(
    index: int,
    *,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.0,
) -> Candle:
    open_time = datetime(2026, 1, 1, 12, 1, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=100.0,
        high=high,
        low=low,
        close=close,
    )


class CapturingMarketDataProvider:
    def __init__(self, candles: tuple[Candle, ...]) -> None:
        self.query: MarketDataQuery | None = None
        self._candles = candles

    def load_candles(self, query: MarketDataQuery | None = None) -> tuple[Candle, ...]:
        self.query = query
        return self._candles


def test_builds_trade_plan_from_tradingview_payload_execution() -> None:
    plan = trade_plan_from_tradingview_payload(valid_payload())

    assert plan.direction == TradeDirection.LONG
    assert plan.entry_price == 100.0
    assert plan.stop_loss == 95.0
    assert plan.take_profit == 110.0
    assert plan.initial_risk == 5.0


def test_evaluates_tradingview_outcome_with_market_data_provider() -> None:
    provider = CapturingMarketDataProvider(
        (
            make_candle(0, high=101.0, low=99.0),
            make_candle(1, high=111.0, low=100.0),
        )
    )

    evaluation = evaluate_tradingview_outcome(
        valid_payload(),
        provider,
        OutcomeConfig(max_holding_bars=5, entry_timeout_bars=2),
    )

    assert isinstance(provider, MarketDataProvider)
    assert provider.query == MarketDataQuery(
        symbol="BTCUSDT",
        timeframe="1",
        start_time=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
    )
    assert evaluation.event_id == "BTCUSDT-1-1767225660000-LONG"
    assert evaluation.symbol == "BTCUSDT"
    assert evaluation.timeframe == "1"
    assert evaluation.candles_loaded == 2
    assert evaluation.outcome.label == TradeOutcomeLabel.WIN
    assert evaluation.outcome.exit_reason == OutcomeExitReason.TAKE_PROFIT_HIT
    assert evaluation.outcome.realized_r == 2.0


def test_evaluates_tradingview_outcome_against_imported_csv_market_data(tmp_path) -> None:
    csv_path = tmp_path / "btc.csv"
    csv_path.write_text(
        "\n".join(
            [
                "symbol,timeframe,time,open,high,low,close,volume",
                "BTCUSDT,1,2026-01-01T12:00:00Z,99,99.5,98,99,1000",
                "ETHUSDT,1,2026-01-01T12:01:00Z,200,201,199,200,1000",
                "BTCUSDT,1,2026-01-01T12:01:00Z,100,101,99,100.5,1000",
                "BTCUSDT,1,2026-01-01T12:02:00Z,100.5,111,100,110.5,1000",
            ]
        ),
        encoding="utf-8",
    )

    evaluation = evaluate_tradingview_outcome(
        valid_payload(),
        CsvMarketDataProvider(csv_path),
        OutcomeConfig(max_holding_bars=5, entry_timeout_bars=2),
    )

    assert evaluation.candles_loaded == 2
    assert evaluation.outcome.label == TradeOutcomeLabel.WIN
    assert evaluation.outcome.exit_price == 110.0
