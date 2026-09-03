from copy import deepcopy

import pytest
from pydantic import ValidationError

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.enums import TradeDirection


def valid_payload() -> dict[str, object]:
    return {
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
            "bos": False,
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
            "takeProfit": 65780.0,
            "riskReward": 3.0,
        },
        "features": {
            "atr": 285.0,
            "relativeVolume": 1.7,
            "displacementScore": 0.81,
            "session": "NEW_YORK",
        },
    }


def test_accepts_valid_tradingview_setup_candidate_payload() -> None:
    payload = TradingViewWebhookPayload.model_validate(valid_payload())

    assert payload.schema_version == "1.0"
    assert payload.event_id == "BTCUSDT-1m-1720000000-bullish-choch"
    assert payload.source == "TRADINGVIEW"
    assert payload.direction == TradeDirection.LONG
    assert payload.market_structure.liquidity_sweep is True
    assert payload.execution.risk_reward == 3.0
    assert payload.features.displacement_score == 0.81


def test_accepts_short_execution_order() -> None:
    raw_payload = valid_payload()
    raw_payload["direction"] = "SHORT"
    raw_payload["execution"] = {
        "entry": 65180.0,
        "stopLoss": 65380.0,
        "takeProfit": 64580.0,
        "riskReward": 3.0,
    }

    payload = TradingViewWebhookPayload.model_validate(raw_payload)

    assert payload.direction == TradeDirection.SHORT


def test_accepts_pine_prototype_long_candidate_payload_shape() -> None:
    raw_payload = valid_payload()
    raw_payload["eventId"] = "BTCUSDT-1-1767225660000-LONG"
    raw_payload["exchange"] = "UNKNOWN"
    raw_payload["marketStructure"] = {
        "htfTimeframe": "15",
        "htfBias": "BULLISH",
        "bos": True,
        "choch": True,
        "liquiditySweep": False,
    }
    raw_payload["fvg"] = {
        "lower": 100.0,
        "upper": 110.0,
        "equilibrium": 105.0,
        "sizeAtrRatio": 0.0,
        "mitigationPercent": 0.0,
    }
    raw_payload["execution"] = {
        "entry": 105.0,
        "stopLoss": 99.0,
        "takeProfit": 117.0,
        "riskReward": 2.0,
    }
    raw_payload["features"] = {
        "atr": None,
        "relativeVolume": None,
        "displacementScore": 0.0,
        "session": "OFF_HOURS",
    }

    payload = TradingViewWebhookPayload.model_validate(raw_payload)

    assert payload.execution.risk_reward == 2.0
    assert payload.features.atr is None
    assert payload.exchange == "UNKNOWN"


def test_accepts_pine_prototype_short_candidate_payload_shape() -> None:
    raw_payload = valid_payload()
    raw_payload["eventId"] = "BTCUSDT-1-1767225660000-SHORT"
    raw_payload["direction"] = "SHORT"
    raw_payload["marketStructure"] = {
        "htfTimeframe": "15",
        "htfBias": "BEARISH",
        "bos": True,
        "choch": True,
        "liquiditySweep": False,
    }
    raw_payload["fvg"] = {
        "lower": 90.0,
        "upper": 100.0,
        "equilibrium": 95.0,
        "sizeAtrRatio": 0.0,
        "mitigationPercent": 0.0,
    }
    raw_payload["execution"] = {
        "entry": 95.0,
        "stopLoss": 101.0,
        "takeProfit": 83.0,
        "riskReward": 2.0,
    }
    raw_payload["features"] = {
        "atr": None,
        "relativeVolume": None,
        "displacementScore": 0.0,
        "session": "NEW_YORK",
    }

    payload = TradingViewWebhookPayload.model_validate(raw_payload)

    assert payload.direction == TradeDirection.SHORT
    assert payload.execution.risk_reward == 2.0


def test_rejects_unsupported_schema_version() -> None:
    raw_payload = valid_payload()
    raw_payload["schemaVersion"] = "2.0"

    with pytest.raises(ValidationError, match="schemaVersion"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_invalid_timeframe() -> None:
    raw_payload = valid_payload()
    raw_payload["timeframe"] = "0"

    with pytest.raises(ValidationError, match="timeframe"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_invalid_htf_timeframe() -> None:
    raw_payload = valid_payload()
    market_structure = deepcopy(raw_payload["marketStructure"])
    assert isinstance(market_structure, dict)
    market_structure["htfTimeframe"] = "intraday"
    raw_payload["marketStructure"] = market_structure

    with pytest.raises(ValidationError, match="htfTimeframe"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_extra_payload_fields_to_keep_contract_explicit() -> None:
    raw_payload = valid_payload()
    raw_payload["secret"] = "must-not-be-accepted"

    with pytest.raises(ValidationError, match="Extra inputs"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_non_chronological_bar_times() -> None:
    raw_payload = valid_payload()
    raw_payload["barCloseTime"] = raw_payload["barOpenTime"]

    with pytest.raises(ValidationError, match="barCloseTime"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_long_execution_with_stop_above_entry() -> None:
    raw_payload = valid_payload()
    raw_payload["execution"] = {
        "entry": 65180.0,
        "stopLoss": 65200.0,
        "takeProfit": 65780.0,
        "riskReward": 3.0,
    }

    with pytest.raises(ValidationError, match="LONG execution"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_execution_when_risk_reward_does_not_match_prices() -> None:
    raw_payload = valid_payload()
    raw_payload["execution"] = {
        "entry": 65180.0,
        "stopLoss": 64980.0,
        "takeProfit": 65780.0,
        "riskReward": 2.0,
    }

    with pytest.raises(ValidationError, match="riskReward"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_short_execution_with_target_above_entry() -> None:
    raw_payload = valid_payload()
    raw_payload["direction"] = "SHORT"
    raw_payload["execution"] = {
        "entry": 65180.0,
        "stopLoss": 65380.0,
        "takeProfit": 65780.0,
        "riskReward": 3.0,
    }

    with pytest.raises(ValidationError, match="SHORT execution"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_rejects_invalid_fvg_bounds() -> None:
    raw_payload = valid_payload()
    raw_payload["fvg"] = {
        "lower": 65240.0,
        "upper": 65120.0,
        "equilibrium": 65180.0,
        "sizeAtrRatio": 0.42,
        "mitigationPercent": 0.0,
    }

    with pytest.raises(ValidationError, match="fvg.lower"):
        TradingViewWebhookPayload.model_validate(raw_payload)


def test_exports_json_schema_with_camel_case_contract_fields() -> None:
    schema = TradingViewWebhookPayload.model_json_schema(by_alias=True)

    assert "schemaVersion" in schema["properties"]
    assert "eventId" in schema["properties"]
    assert "marketStructure" in schema["properties"]
    assert "bar_open_time" not in schema["properties"]
