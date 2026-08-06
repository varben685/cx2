import pytest

from smc_assistant.domain.risk import calculate_realized_r, calculate_risk_reward


def test_calculate_risk_reward_for_long_plan() -> None:
    result = calculate_risk_reward(entry_price=100.0, stop_loss=95.0, take_profit=115.0)

    assert result.initial_risk == 5.0
    assert result.planned_reward == 15.0
    assert result.risk_reward == 3.0


def test_calculate_risk_reward_rejects_zero_risk() -> None:
    with pytest.raises(ValueError, match="Initial risk"):
        calculate_risk_reward(entry_price=100.0, stop_loss=100.0, take_profit=115.0)


def test_calculate_realized_r() -> None:
    assert calculate_realized_r(realized_profit_or_loss=12.5, initial_risk=5.0) == 2.5

