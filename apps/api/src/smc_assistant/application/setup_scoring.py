from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.market_structure import MarketBias
from smc_assistant.domain.setup_scoring import (
    SetupScore,
    SetupScoringConfig,
    SetupScoringInput,
    TradingSession,
    score_setup_candidate,
)


def scoring_input_from_tradingview_payload(
    payload: TradingViewWebhookPayload,
) -> SetupScoringInput:
    return SetupScoringInput(
        direction=payload.direction,
        htf_bias=MarketBias(payload.market_structure.htf_bias.value),
        choch=payload.market_structure.choch,
        liquidity_sweep=payload.market_structure.liquidity_sweep,
        displacement_score=payload.features.displacement_score,
        fvg_size_atr_ratio=payload.fvg.size_atr_ratio,
        session=TradingSession(payload.features.session.value),
        risk_reward=payload.execution.risk_reward,
    )


def score_tradingview_payload(
    payload: TradingViewWebhookPayload,
    config: SetupScoringConfig | None = None,
) -> SetupScore:
    return score_setup_candidate(
        scoring_input_from_tradingview_payload(payload),
        config,
    )
