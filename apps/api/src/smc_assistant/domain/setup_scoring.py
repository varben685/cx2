from dataclasses import dataclass
from enum import StrEnum

from smc_assistant.domain.enums import TradeDirection
from smc_assistant.domain.market_structure import MarketBias


class TradingSession(StrEnum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OFF_HOURS = "OFF_HOURS"


class ScoreComponentName(StrEnum):
    HTF_BIAS = "HTF_BIAS"
    CHOCH = "CHOCH"
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"
    DISPLACEMENT = "DISPLACEMENT"
    FVG_SIZE = "FVG_SIZE"
    SESSION = "SESSION"
    RISK_REWARD = "RISK_REWARD"


class SetupRejectionReason(StrEnum):
    HTF_BIAS_CONFLICT = "HTF_BIAS_CONFLICT"
    MISSING_CHOCH = "MISSING_CHOCH"
    RISK_REWARD_TOO_LOW = "RISK_REWARD_TOO_LOW"
    SCORE_BELOW_THRESHOLD = "SCORE_BELOW_THRESHOLD"


@dataclass(frozen=True, slots=True)
class SetupScoringConfig:
    strategy_version: str = "smc-rce-v1"
    config_version: str = "rule-score-v1"
    acceptance_threshold: float = 70.0
    minimum_risk_reward: float = 2.0
    displacement_target_score: float = 0.65
    fvg_size_atr_target: float = 0.25
    htf_bias_weight: float = 20.0
    choch_weight: float = 20.0
    liquidity_sweep_weight: float = 15.0
    displacement_weight: float = 20.0
    fvg_size_weight: float = 10.0
    session_weight: float = 10.0
    risk_reward_weight: float = 5.0

    def __post_init__(self) -> None:
        if not 0 <= self.acceptance_threshold <= 100:
            raise ValueError("acceptance_threshold must be between 0 and 100.")

        positive_values = {
            "minimum_risk_reward": self.minimum_risk_reward,
            "displacement_target_score": self.displacement_target_score,
            "fvg_size_atr_target": self.fvg_size_atr_target,
        }
        for name, value in positive_values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")

        weights = [
            self.htf_bias_weight,
            self.choch_weight,
            self.liquidity_sweep_weight,
            self.displacement_weight,
            self.fvg_size_weight,
            self.session_weight,
            self.risk_reward_weight,
        ]
        if any(weight < 0 for weight in weights):
            raise ValueError("Score weights must be non-negative.")

        if abs(sum(weights) - 100.0) > 0.001:
            raise ValueError("Score weights must sum to 100.")


@dataclass(frozen=True, slots=True)
class SetupScoringInput:
    direction: TradeDirection
    htf_bias: MarketBias
    choch: bool
    liquidity_sweep: bool
    displacement_score: float
    fvg_size_atr_ratio: float
    session: TradingSession
    risk_reward: float

    def __post_init__(self) -> None:
        if not 0 <= self.displacement_score <= 1:
            raise ValueError("displacement_score must be between 0 and 1.")

        if self.fvg_size_atr_ratio < 0:
            raise ValueError("fvg_size_atr_ratio must be non-negative.")

        if self.risk_reward <= 0:
            raise ValueError("risk_reward must be greater than zero.")


@dataclass(frozen=True, slots=True)
class ScoreComponent:
    name: ScoreComponentName
    score: float
    max_score: float
    reason: str


@dataclass(frozen=True, slots=True)
class SetupScore:
    score: float
    accepted: bool
    strategy_version: str
    config_version: str
    components: tuple[ScoreComponent, ...]
    rejection_reasons: tuple[SetupRejectionReason, ...]
    positive_reasons: tuple[str, ...]
    negative_reasons: tuple[str, ...]


def score_setup_candidate(
    scoring_input: SetupScoringInput,
    config: SetupScoringConfig | None = None,
) -> SetupScore:
    scoring_config = config or SetupScoringConfig()
    rejection_reasons: list[SetupRejectionReason] = []

    components = [
        _score_htf_bias(scoring_input, scoring_config, rejection_reasons),
        _score_boolean_component(
            name=ScoreComponentName.CHOCH,
            present=scoring_input.choch,
            max_score=scoring_config.choch_weight,
            positive_reason="CHoCH is present.",
            negative_reason="CHoCH is missing.",
        ),
        _score_boolean_component(
            name=ScoreComponentName.LIQUIDITY_SWEEP,
            present=scoring_input.liquidity_sweep,
            max_score=scoring_config.liquidity_sweep_weight,
            positive_reason="Liquidity sweep is present.",
            negative_reason="Liquidity sweep is missing.",
        ),
        _score_ratio_component(
            name=ScoreComponentName.DISPLACEMENT,
            value=scoring_input.displacement_score,
            target=scoring_config.displacement_target_score,
            max_score=scoring_config.displacement_weight,
            reason="Displacement score relative to target.",
        ),
        _score_ratio_component(
            name=ScoreComponentName.FVG_SIZE,
            value=scoring_input.fvg_size_atr_ratio,
            target=scoring_config.fvg_size_atr_target,
            max_score=scoring_config.fvg_size_weight,
            reason="FVG size/ATR ratio relative to target.",
        ),
        _score_session(scoring_input.session, scoring_config.session_weight),
        _score_ratio_component(
            name=ScoreComponentName.RISK_REWARD,
            value=scoring_input.risk_reward,
            target=scoring_config.minimum_risk_reward,
            max_score=scoring_config.risk_reward_weight,
            reason="Risk-reward relative to minimum target.",
        ),
    ]

    if not scoring_input.choch:
        rejection_reasons.append(SetupRejectionReason.MISSING_CHOCH)

    if scoring_input.risk_reward < scoring_config.minimum_risk_reward:
        rejection_reasons.append(SetupRejectionReason.RISK_REWARD_TOO_LOW)

    total_score = round(sum(component.score for component in components), 2)
    if total_score < scoring_config.acceptance_threshold:
        rejection_reasons.append(SetupRejectionReason.SCORE_BELOW_THRESHOLD)

    positive_reasons = tuple(
        component.reason for component in components if component.score >= component.max_score
    )
    negative_reasons = tuple(
        component.reason for component in components if component.score < component.max_score
    )

    return SetupScore(
        score=total_score,
        accepted=not rejection_reasons,
        strategy_version=scoring_config.strategy_version,
        config_version=scoring_config.config_version,
        components=tuple(components),
        rejection_reasons=tuple(rejection_reasons),
        positive_reasons=positive_reasons,
        negative_reasons=negative_reasons,
    )


def _score_htf_bias(
    scoring_input: SetupScoringInput,
    config: SetupScoringConfig,
    rejection_reasons: list[SetupRejectionReason],
) -> ScoreComponent:
    expected_bias = (
        MarketBias.BULLISH
        if scoring_input.direction == TradeDirection.LONG
        else MarketBias.BEARISH
    )
    if scoring_input.htf_bias == expected_bias:
        return ScoreComponent(
            name=ScoreComponentName.HTF_BIAS,
            score=config.htf_bias_weight,
            max_score=config.htf_bias_weight,
            reason="HTF bias aligns with setup direction.",
        )

    if scoring_input.htf_bias == MarketBias.NEUTRAL:
        return ScoreComponent(
            name=ScoreComponentName.HTF_BIAS,
            score=config.htf_bias_weight * 0.5,
            max_score=config.htf_bias_weight,
            reason="HTF bias is neutral.",
        )

    rejection_reasons.append(SetupRejectionReason.HTF_BIAS_CONFLICT)
    return ScoreComponent(
        name=ScoreComponentName.HTF_BIAS,
        score=0.0,
        max_score=config.htf_bias_weight,
        reason="HTF bias conflicts with setup direction.",
    )


def _score_boolean_component(
    *,
    name: ScoreComponentName,
    present: bool,
    max_score: float,
    positive_reason: str,
    negative_reason: str,
) -> ScoreComponent:
    return ScoreComponent(
        name=name,
        score=max_score if present else 0.0,
        max_score=max_score,
        reason=positive_reason if present else negative_reason,
    )


def _score_ratio_component(
    *,
    name: ScoreComponentName,
    value: float,
    target: float,
    max_score: float,
    reason: str,
) -> ScoreComponent:
    return ScoreComponent(
        name=name,
        score=round(max_score * min(value / target, 1.0), 2),
        max_score=max_score,
        reason=reason,
    )


def _score_session(session: TradingSession, max_score: float) -> ScoreComponent:
    if session in {TradingSession.LONDON, TradingSession.NEW_YORK}:
        return ScoreComponent(
            name=ScoreComponentName.SESSION,
            score=max_score,
            max_score=max_score,
            reason="Session is liquid.",
        )

    if session == TradingSession.ASIA:
        return ScoreComponent(
            name=ScoreComponentName.SESSION,
            score=max_score * 0.5,
            max_score=max_score,
            reason="Session is acceptable but not primary.",
        )

    return ScoreComponent(
        name=ScoreComponentName.SESSION,
        score=0.0,
        max_score=max_score,
        reason="Session is off-hours.",
    )
