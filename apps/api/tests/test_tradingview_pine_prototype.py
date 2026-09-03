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


def test_pine_prototype_uses_clean_defaults() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert 'leftBars = input.int(5, "Left bars"' in source
    assert 'rightBars = input.int(5, "Right bars"' in source
    assert 'showSwings = input.bool(false, "Show swings")' in source
    assert 'showBosLabels = input.bool(false, "Show BOS labels")' in source
    assert 'showChochLabels = input.bool(true, "Show CHoCH labels")' in source
    assert 'showOnlySetupFvgs = input.bool(true, "Only setup FVGs")' in source
    assert 'showSweeps = input.bool(false, "Show liquidity sweeps")' in source
    assert 'showDisplacement = input.bool(false, "Show displacement")' in source


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


def test_pine_prototype_avoids_multiline_calls_that_break_tradingview() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    fragile_multiline_calls = [
        "indicator(\n",
        "label.new(\n",
        "box.new(\n",
        "plotshape(\n",
    ]

    for fragile_call in fragile_multiline_calls:
        assert fragile_call not in source
