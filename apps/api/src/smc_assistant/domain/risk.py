from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskReward:
    initial_risk: float
    planned_reward: float
    risk_reward: float


def calculate_risk_reward(entry_price: float, stop_loss: float, take_profit: float) -> RiskReward:
    initial_risk = abs(entry_price - stop_loss)
    if initial_risk <= 0:
        raise ValueError("Initial risk must be greater than zero.")

    planned_reward = abs(take_profit - entry_price)
    if planned_reward <= 0:
        raise ValueError("Planned reward must be greater than zero.")

    return RiskReward(
        initial_risk=initial_risk,
        planned_reward=planned_reward,
        risk_reward=planned_reward / initial_risk,
    )


def calculate_realized_r(realized_profit_or_loss: float, initial_risk: float) -> float:
    if initial_risk <= 0:
        raise ValueError("Initial risk must be greater than zero.")

    return realized_profit_or_loss / initial_risk

