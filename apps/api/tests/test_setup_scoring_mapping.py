from smc_assistant.application.setup_scoring import (
    score_tradingview_payload,
    scoring_input_from_tradingview_payload,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.enums import TradeDirection
from smc_assistant.domain.market_structure import MarketBias
from smc_assistant.domain.setup_scoring import TradingSession


def valid_payload() -> TradingViewWebhookPayload:
    return TradingViewWebhookPayload.model_validate(
        {
            "schemaVersion": "1.0",
            "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
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
                "lower": 65120.0,
                "upper": 65240.0,
                "equilibrium": 65180.0,
                "sizeAtrRatio": 0.42,
                "mitigationPercent": 0.0,
            },
            "execution": {
                "entry": 65180.0,
                "stopLoss": 64980.0,
                "takeProfit": 65580.0,
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


def test_maps_tradingview_payload_to_setup_scoring_input() -> None:
    scoring_input = scoring_input_from_tradingview_payload(valid_payload())

    assert scoring_input.direction == TradeDirection.LONG
    assert scoring_input.htf_bias == MarketBias.BULLISH
    assert scoring_input.choch is True
    assert scoring_input.liquidity_sweep is True
    assert scoring_input.displacement_score == 0.81
    assert scoring_input.fvg_size_atr_ratio == 0.42
    assert scoring_input.session == TradingSession.NEW_YORK
    assert scoring_input.risk_reward == 2.0


def test_scores_tradingview_payload() -> None:
    score = score_tradingview_payload(valid_payload())

    assert score.accepted is True
    assert score.score == 100.0
    assert score.config_version == "rule-score-v1"
