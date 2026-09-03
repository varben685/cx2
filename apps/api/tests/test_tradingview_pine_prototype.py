from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PINE_PROTOTYPE = REPO_ROOT / "tradingview" / "indicators" / "smc_assistant_prototype.pine"


def test_pine_prototype_exists() -> None:
    assert PINE_PROTOTYPE.exists()


def test_pine_prototype_declares_expected_visual_components() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "ta.pivothigh" in source
    assert "ta.pivotlow" in source
    assert "bullishBos" in source
    assert "bearishBos" in source
    assert "bullishFvg" in source
    assert "bearishFvg" in source
    assert "bullishSweep" in source
    assert "bearishSweep" in source
    assert "displacementScore" in source


def test_pine_alert_payload_contains_backend_contract_keys() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    expected_keys = [
        "schemaVersion",
        "eventId",
        "eventType",
        "source",
        "strategyVersion",
        "symbol",
        "exchange",
        "timeframe",
        "barOpenTime",
        "barCloseTime",
        "direction",
        "marketStructure",
        "htfTimeframe",
        "htfBias",
        "liquiditySweep",
        "execution",
        "riskReward",
        "features",
        "displacementScore",
    ]

    for expected_key in expected_keys:
        assert expected_key in source


def test_pine_alert_payload_uses_non_placeholder_execution_values() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "riskRewardPlaceholder" not in source
    assert "setupEntry" in source
    assert "setupStopLoss" in source
    assert "setupTakeProfit" in source
    assert "setupRiskReward" in source
