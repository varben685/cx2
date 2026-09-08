from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


class RiskRejectionReason(StrEnum):
    SETUP_REJECTED = "SETUP_REJECTED"
    SCORE_TOO_LOW = "SCORE_TOO_LOW"
    RISK_PER_TRADE_EXCEEDED = "RISK_PER_TRADE_EXCEEDED"
    RISK_REWARD_TOO_LOW = "RISK_REWARD_TOO_LOW"
    SESSION_NOT_ALLOWED = "SESSION_NOT_ALLOWED"
    MAX_OPEN_POSITIONS = "MAX_OPEN_POSITIONS"
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"
    MAX_CONSECUTIVE_LOSSES = "MAX_CONSECUTIVE_LOSSES"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    CORRELATED_POSITION_LIMIT = "CORRELATED_POSITION_LIMIT"


@dataclass(frozen=True, slots=True)
class RiskPolicyConfig:
    version: str = "paper-risk-v1"
    max_risk_per_trade_percent: float = 1.0
    max_daily_loss_r: float = 3.0
    max_consecutive_losses: int = 3
    minimum_risk_reward: float = 2.0
    max_open_positions: int = 3
    cooldown_minutes: int = 15
    setup_score_minimum: float = 70.0
    allowed_sessions: tuple[str, ...] = ("ASIA", "LONDON", "NEW_YORK")
    correlation_groups: tuple[tuple[str, ...], ...] = ()
    max_correlated_positions: int = 1

    def __post_init__(self) -> None:
        if min(
            self.max_risk_per_trade_percent,
            self.max_daily_loss_r,
            self.minimum_risk_reward,
            self.setup_score_minimum,
        ) <= 0:
            raise ValueError("Paper risk policy numeric thresholds must be positive.")
        if min(
            self.max_consecutive_losses,
            self.max_open_positions,
            self.max_correlated_positions,
        ) < 1:
            raise ValueError("Paper risk policy count limits must be positive.")
        if self.cooldown_minutes < 0:
            raise ValueError("Paper risk policy cooldown must not be negative.")
        if not self.allowed_sessions:
            raise ValueError("Paper risk policy must allow at least one session.")


@dataclass(frozen=True, slots=True)
class OpenPositionRisk:
    symbol: str


@dataclass(frozen=True, slots=True)
class ClosedTradeRisk:
    symbol: str
    closed_at: datetime
    realized_r: float


@dataclass(frozen=True, slots=True)
class RiskPolicyInput:
    setup_accepted: bool
    setup_score: float
    risk_percent: float
    planned_risk_reward: float
    session: str
    symbol: str
    evaluated_at: datetime
    open_positions: tuple[OpenPositionRisk, ...] = ()
    closed_trades: tuple[ClosedTradeRisk, ...] = ()


@dataclass(frozen=True, slots=True)
class RiskPolicyDecision:
    approved: bool
    policy_version: str
    rejection_reasons: tuple[RiskRejectionReason, ...]
    daily_loss_r: float
    consecutive_losses: int
    open_positions: int


def evaluate_risk_policy(
    policy_input: RiskPolicyInput,
    config: RiskPolicyConfig | None = None,
) -> RiskPolicyDecision:
    selected = config or RiskPolicyConfig()
    reasons: list[RiskRejectionReason] = []
    if not policy_input.setup_accepted:
        reasons.append(RiskRejectionReason.SETUP_REJECTED)
    if policy_input.setup_score < selected.setup_score_minimum:
        reasons.append(RiskRejectionReason.SCORE_TOO_LOW)
    if policy_input.risk_percent > selected.max_risk_per_trade_percent:
        reasons.append(RiskRejectionReason.RISK_PER_TRADE_EXCEEDED)
    if policy_input.planned_risk_reward < selected.minimum_risk_reward:
        reasons.append(RiskRejectionReason.RISK_REWARD_TOO_LOW)
    if policy_input.session not in selected.allowed_sessions:
        reasons.append(RiskRejectionReason.SESSION_NOT_ALLOWED)
    if len(policy_input.open_positions) >= selected.max_open_positions:
        reasons.append(RiskRejectionReason.MAX_OPEN_POSITIONS)

    todays_closed = tuple(
        trade
        for trade in policy_input.closed_trades
        if trade.closed_at.date() == policy_input.evaluated_at.date()
    )
    daily_loss_r = sum(-trade.realized_r for trade in todays_closed if trade.realized_r < 0)
    if daily_loss_r >= selected.max_daily_loss_r:
        reasons.append(RiskRejectionReason.MAX_DAILY_LOSS)

    consecutive_losses = 0
    for trade in sorted(policy_input.closed_trades, key=lambda item: item.closed_at, reverse=True):
        if trade.realized_r >= 0:
            break
        consecutive_losses += 1
    if consecutive_losses >= selected.max_consecutive_losses:
        reasons.append(RiskRejectionReason.MAX_CONSECUTIVE_LOSSES)

    matching_closes = [
        trade.closed_at
        for trade in policy_input.closed_trades
        if trade.symbol == policy_input.symbol
    ]
    if matching_closes and policy_input.evaluated_at - max(matching_closes) < timedelta(
        minutes=selected.cooldown_minutes
    ):
        reasons.append(RiskRejectionReason.COOLDOWN_ACTIVE)

    group = next(
        (items for items in selected.correlation_groups if policy_input.symbol in items),
        None,
    )
    if group is not None:
        correlated_open = sum(
            position.symbol in group for position in policy_input.open_positions
        )
        if correlated_open >= selected.max_correlated_positions:
            reasons.append(RiskRejectionReason.CORRELATED_POSITION_LIMIT)

    return RiskPolicyDecision(
        approved=not reasons,
        policy_version=selected.version,
        rejection_reasons=tuple(reasons),
        daily_loss_r=round(daily_loss_r, 6),
        consecutive_losses=consecutive_losses,
        open_positions=len(policy_input.open_positions),
    )
