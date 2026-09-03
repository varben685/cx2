import pytest

from smc_assistant.domain.enums import TradeDirection
from smc_assistant.domain.market_structure import MarketBias
from smc_assistant.domain.setup_scoring import (
    ScoreComponentName,
    SetupRejectionReason,
    SetupScoringConfig,
    SetupScoringInput,
    TradingSession,
    score_setup_candidate,
)


def strong_long_input() -> SetupScoringInput:
    return SetupScoringInput(
        direction=TradeDirection.LONG,
        htf_bias=MarketBias.BULLISH,
        choch=True,
        liquidity_sweep=True,
        displacement_score=0.8,
        fvg_size_atr_ratio=0.35,
        session=TradingSession.NEW_YORK,
        risk_reward=3.0,
    )


def test_scores_strong_aligned_setup_as_accepted() -> None:
    result = score_setup_candidate(strong_long_input())

    assert result.score == 100.0
    assert result.accepted is True
    assert result.strategy_version == "smc-rce-v1"
    assert result.config_version == "rule-score-v1"
    assert result.rejection_reasons == ()
    assert len(result.components) == 7


def test_neutral_htf_bias_is_partial_context_not_hard_rejection() -> None:
    scoring_input = strong_long_input()
    neutral_input = SetupScoringInput(
        direction=scoring_input.direction,
        htf_bias=MarketBias.NEUTRAL,
        choch=scoring_input.choch,
        liquidity_sweep=scoring_input.liquidity_sweep,
        displacement_score=scoring_input.displacement_score,
        fvg_size_atr_ratio=scoring_input.fvg_size_atr_ratio,
        session=scoring_input.session,
        risk_reward=scoring_input.risk_reward,
    )

    result = score_setup_candidate(neutral_input)

    assert result.score == 90.0
    assert result.accepted is True
    assert SetupRejectionReason.HTF_BIAS_CONFLICT not in result.rejection_reasons
    assert "HTF bias is neutral." in result.negative_reasons


def test_rejects_setup_when_htf_bias_conflicts_with_direction() -> None:
    scoring_input = strong_long_input()
    conflicted_input = SetupScoringInput(
        direction=scoring_input.direction,
        htf_bias=MarketBias.BEARISH,
        choch=scoring_input.choch,
        liquidity_sweep=scoring_input.liquidity_sweep,
        displacement_score=scoring_input.displacement_score,
        fvg_size_atr_ratio=scoring_input.fvg_size_atr_ratio,
        session=scoring_input.session,
        risk_reward=scoring_input.risk_reward,
    )

    result = score_setup_candidate(conflicted_input)

    assert result.accepted is False
    assert SetupRejectionReason.HTF_BIAS_CONFLICT in result.rejection_reasons
    assert "HTF bias conflicts with setup direction." in result.negative_reasons


def test_rejects_setup_without_choch() -> None:
    scoring_input = strong_long_input()
    missing_choch_input = SetupScoringInput(
        direction=scoring_input.direction,
        htf_bias=scoring_input.htf_bias,
        choch=False,
        liquidity_sweep=scoring_input.liquidity_sweep,
        displacement_score=scoring_input.displacement_score,
        fvg_size_atr_ratio=scoring_input.fvg_size_atr_ratio,
        session=scoring_input.session,
        risk_reward=scoring_input.risk_reward,
    )

    result = score_setup_candidate(missing_choch_input)

    assert result.accepted is False
    assert SetupRejectionReason.MISSING_CHOCH in result.rejection_reasons
    assert "CHoCH is missing." in result.negative_reasons


def test_rejects_setup_below_minimum_risk_reward() -> None:
    scoring_input = strong_long_input()
    low_rr_input = SetupScoringInput(
        direction=scoring_input.direction,
        htf_bias=scoring_input.htf_bias,
        choch=scoring_input.choch,
        liquidity_sweep=scoring_input.liquidity_sweep,
        displacement_score=scoring_input.displacement_score,
        fvg_size_atr_ratio=scoring_input.fvg_size_atr_ratio,
        session=scoring_input.session,
        risk_reward=1.2,
    )

    result = score_setup_candidate(low_rr_input)
    risk_reward_component = next(
        component
        for component in result.components
        if component.name == ScoreComponentName.RISK_REWARD
    )

    assert result.accepted is False
    assert SetupRejectionReason.RISK_REWARD_TOO_LOW in result.rejection_reasons
    assert risk_reward_component.score == 3.0


def test_low_quality_setup_is_rejected_below_score_threshold() -> None:
    result = score_setup_candidate(
        SetupScoringInput(
            direction=TradeDirection.SHORT,
            htf_bias=MarketBias.NEUTRAL,
            choch=True,
            liquidity_sweep=False,
            displacement_score=0.2,
            fvg_size_atr_ratio=0.0,
            session=TradingSession.OFF_HOURS,
            risk_reward=2.0,
        )
    )

    assert result.score == 41.15
    assert result.accepted is False
    assert SetupRejectionReason.SCORE_BELOW_THRESHOLD in result.rejection_reasons


def test_rejects_scoring_config_when_weights_do_not_sum_to_100() -> None:
    with pytest.raises(ValueError, match="sum to 100"):
        SetupScoringConfig(htf_bias_weight=21.0)


def test_rejects_invalid_scoring_input_values() -> None:
    with pytest.raises(ValueError, match="displacement_score"):
        SetupScoringInput(
            direction=TradeDirection.LONG,
            htf_bias=MarketBias.BULLISH,
            choch=True,
            liquidity_sweep=True,
            displacement_score=1.1,
            fvg_size_atr_ratio=0.1,
            session=TradingSession.LONDON,
            risk_reward=2.0,
        )
