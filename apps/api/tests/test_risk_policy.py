from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from smc_assistant.domain.risk_policy import (
    ClosedTradeRisk,
    OpenPositionRisk,
    RiskPolicyConfig,
    RiskPolicyInput,
    RiskRejectionReason,
    evaluate_risk_policy,
)

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


def valid_input() -> RiskPolicyInput:
    return RiskPolicyInput(
        setup_accepted=True,
        setup_score=85,
        risk_percent=1,
        planned_risk_reward=2,
        session="NEW_YORK",
        symbol="BTCUSDT",
        evaluated_at=NOW,
    )


def test_approves_trade_within_all_risk_limits() -> None:
    decision = evaluate_risk_policy(valid_input())

    assert decision.approved is True
    assert decision.policy_version == "paper-risk-v1"
    assert decision.rejection_reasons == ()


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"setup_accepted": False}, RiskRejectionReason.SETUP_REJECTED),
        ({"setup_score": 69}, RiskRejectionReason.SCORE_TOO_LOW),
        ({"risk_percent": 1.01}, RiskRejectionReason.RISK_PER_TRADE_EXCEEDED),
        ({"planned_risk_reward": 1.99}, RiskRejectionReason.RISK_REWARD_TOO_LOW),
        ({"session": "OFF_HOURS"}, RiskRejectionReason.SESSION_NOT_ALLOWED),
        (
            {"open_positions": tuple(OpenPositionRisk(str(index)) for index in range(3))},
            RiskRejectionReason.MAX_OPEN_POSITIONS,
        ),
    ],
)
def test_rejects_each_static_risk_limit(
    changes: dict[str, object],
    reason: RiskRejectionReason,
) -> None:
    decision = evaluate_risk_policy(replace(valid_input(), **changes))

    assert decision.approved is False
    assert reason in decision.rejection_reasons


def test_rejects_daily_loss_streak_cooldown_and_correlation_limits() -> None:
    closed = tuple(
        ClosedTradeRisk(
            symbol="BTCUSDT",
            closed_at=NOW - timedelta(minutes=index + 1),
            realized_r=-1,
        )
        for index in range(3)
    )
    config = RiskPolicyConfig(correlation_groups=(("BTCUSDT", "ETHUSDT"),))
    decision = evaluate_risk_policy(
        replace(
            valid_input(),
            open_positions=(OpenPositionRisk("ETHUSDT"),),
            closed_trades=closed,
        ),
        config,
    )

    assert decision.daily_loss_r == 3
    assert decision.consecutive_losses == 3
    assert decision.rejection_reasons == (
        RiskRejectionReason.MAX_DAILY_LOSS,
        RiskRejectionReason.MAX_CONSECUTIVE_LOSSES,
        RiskRejectionReason.COOLDOWN_ACTIVE,
        RiskRejectionReason.CORRELATED_POSITION_LIMIT,
    )
