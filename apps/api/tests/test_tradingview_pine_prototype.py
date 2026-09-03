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

    assert 'leftBars = input.int(3, "Left bars"' in source
    assert 'rightBars = input.int(3, "Right bars"' in source
    assert 'showSwings = input.bool(false, "Show swings")' in source
    assert 'showBosLabels = input.bool(true, "Show BOS labels")' in source
    assert 'showChochLabels = input.bool(true, "Show CHoCH labels")' in source
    assert 'showOnlySetupFvgs = input.bool(false, "Only setup FVGs")' in source
    assert 'showStructureLevels = input.bool(true, "Show latest structure levels")' in source
    assert 'showBiasBadge = input.bool(true, "Show bias badge")' in source
    assert 'showSweeps = input.bool(false, "Show liquidity sweeps")' in source
    assert 'showDisplacement = input.bool(false, "Show displacement")' in source
    assert 'maxVisibleFvgs = input.int(8, "Max visible FVGs"' in source


def test_pine_prototype_shows_latest_structure_context() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "var line lastSwingHighLine = na" in source
    assert "var line lastSwingLowLine = na" in source
    assert "line.new(lastSwingHighBar" in source
    assert "line.new(lastSwingLowBar" in source
    assert "extend=extend.right" in source
    assert "Bias: " in source


def test_pine_prototype_uses_watched_swing_levels_for_breaks() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "watchedSwingHighPrice = lastSwingHighPrice" in source
    assert "watchedSwingLowPrice = lastSwingLowPrice" in source
    assert "bullishBos = not na(watchedSwingHighPrice)" in source
    assert "bearishBos = not na(watchedSwingLowPrice)" in source
    assert "brokenSwingHighBar := watchedSwingHighBar" in source
    assert "brokenSwingLowBar := watchedSwingLowBar" in source


def test_pine_prototype_bootstraps_neutral_bias_from_swing_sequence() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "var float previousSwingHighPrice = na" in source
    assert "var float previousSwingLowPrice = na" in source
    assert "previousSwingHighPrice := lastSwingHighPrice" in source
    assert "previousSwingLowPrice := lastSwingLowPrice" in source
    assert "bullishSwingSequence" in source
    assert "bearishSwingSequence" in source
    assert "if marketBias == 0 and bullishSwingSequence" in source
    assert "if marketBias == 0 and bearishSwingSequence" in source


def test_pine_prototype_caps_visible_fvg_boxes() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert "var box[] fvgBoxes = array.new_box()" in source
    assert "array.push(fvgBoxes" in source
    assert "array.size(fvgBoxes) > maxVisibleFvgs" in source
    assert "box.delete(array.shift(fvgBoxes))" in source


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


def test_pine_alert_payload_avoids_invalid_optional_json_values() -> None:
    source = PINE_PROTOTYPE.read_text(encoding="utf-8")

    assert 'exchangeName = syminfo.prefix == "" ? "UNKNOWN" : syminfo.prefix' in source
    assert '"exchange":"\' + exchangeName' in source
    assert 'jsonAtr = na(priorAtr) ? "null" : str.tostring(priorAtr)' in source
    assert '"features":{"atr":\' + jsonAtr' in source


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
