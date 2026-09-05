from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from smc_assistant.domain.candles import Candle
from smc_assistant.domain.enums import TradeDirection, TradeOutcomeLabel
from smc_assistant.domain.risk import calculate_realized_r


class OutcomeExitReason(StrEnum):
    TAKE_PROFIT_HIT = "TAKE_PROFIT_HIT"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    VERTICAL_BARRIER_HIT = "VERTICAL_BARRIER_HIT"
    ENTRY_NOT_TRIGGERED = "ENTRY_NOT_TRIGGERED"


@dataclass(frozen=True, slots=True)
class TradePlan:
    direction: TradeDirection
    entry_price: float
    stop_loss: float
    take_profit: float

    def __post_init__(self) -> None:
        prices = {
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
        }
        for name, value in prices.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero.")

        if self.direction == TradeDirection.LONG:
            if not self.stop_loss < self.entry_price < self.take_profit:
                raise ValueError("Long trade requires stop_loss < entry_price < take_profit.")
        else:
            if not self.take_profit < self.entry_price < self.stop_loss:
                raise ValueError("Short trade requires take_profit < entry_price < stop_loss.")

    @property
    def initial_risk(self) -> float:
        return abs(self.entry_price - self.stop_loss)


@dataclass(frozen=True, slots=True)
class OutcomeConfig:
    max_holding_bars: int = 30
    entry_timeout_bars: int = 5
    commission_bps_per_side: float = 0.0
    slippage_bps_per_side: float = 0.0

    def __post_init__(self) -> None:
        if self.max_holding_bars <= 0:
            raise ValueError("max_holding_bars must be greater than zero.")

        if self.entry_timeout_bars <= 0:
            raise ValueError("entry_timeout_bars must be greater than zero.")

        if self.commission_bps_per_side < 0:
            raise ValueError("commission_bps_per_side must be non-negative.")

        if self.slippage_bps_per_side < 0:
            raise ValueError("slippage_bps_per_side must be non-negative.")


@dataclass(frozen=True, slots=True)
class TradeCostEstimate:
    commission_amount: float
    slippage_amount: float
    total_amount: float
    cost_r: float


@dataclass(frozen=True, slots=True)
class TradeExcursion:
    mfe_r: float
    mae_r: float
    max_favorable_price: float
    max_adverse_price: float


@dataclass(frozen=True, slots=True)
class TradeOutcome:
    label: TradeOutcomeLabel
    exit_reason: OutcomeExitReason
    realized_r: float | None
    net_realized_r: float | None
    costs: TradeCostEstimate | None
    excursion: TradeExcursion | None
    entry_time: datetime | None
    exit_time: datetime | None
    exit_price: float | None
    bars_to_entry: int | None
    bars_held: int | None


def evaluate_triple_barrier_outcome(
    plan: TradePlan,
    future_candles: Sequence[Candle],
    config: OutcomeConfig | None = None,
) -> TradeOutcome:
    outcome_config = config or OutcomeConfig()
    _ensure_chronological(future_candles)

    entry_index = _find_entry_index(
        plan=plan,
        candles=future_candles[: outcome_config.entry_timeout_bars],
    )
    if entry_index is None:
        return TradeOutcome(
            label=TradeOutcomeLabel.NOT_TRIGGERED,
            exit_reason=OutcomeExitReason.ENTRY_NOT_TRIGGERED,
            realized_r=None,
            net_realized_r=None,
            costs=None,
            excursion=None,
            entry_time=None,
            exit_time=None,
            exit_price=None,
            bars_to_entry=None,
            bars_held=None,
        )

    entry_candle = future_candles[entry_index]
    evaluation_candles = future_candles[
        entry_index : entry_index + outcome_config.max_holding_bars
    ]
    for held_index, candle in enumerate(evaluation_candles, start=1):
        barrier = _resolve_barrier_hit(plan, candle)
        if barrier is not None:
            label, exit_reason, exit_price = barrier
            realized_r = _calculate_realized_r(plan, exit_price)
            costs = _estimate_trade_costs(plan, exit_price, outcome_config)
            excursion = _calculate_excursion(plan, evaluation_candles[:held_index])
            return TradeOutcome(
                label=label,
                exit_reason=exit_reason,
                realized_r=realized_r,
                net_realized_r=round(realized_r - costs.cost_r, 4),
                costs=costs,
                excursion=excursion,
                entry_time=entry_candle.close_time,
                exit_time=candle.close_time,
                exit_price=exit_price,
                bars_to_entry=entry_index + 1,
                bars_held=held_index,
            )

    timeout_candle = evaluation_candles[-1]
    realized_r = _calculate_realized_r(plan, timeout_candle.close)
    costs = _estimate_trade_costs(plan, timeout_candle.close, outcome_config)
    excursion = _calculate_excursion(plan, evaluation_candles)
    return TradeOutcome(
        label=TradeOutcomeLabel.TIMEOUT,
        exit_reason=OutcomeExitReason.VERTICAL_BARRIER_HIT,
        realized_r=realized_r,
        net_realized_r=round(realized_r - costs.cost_r, 4),
        costs=costs,
        excursion=excursion,
        entry_time=entry_candle.close_time,
        exit_time=timeout_candle.close_time,
        exit_price=timeout_candle.close,
        bars_to_entry=entry_index + 1,
        bars_held=len(evaluation_candles),
    )


def _ensure_chronological(candles: Sequence[Candle]) -> None:
    for previous, current in zip(candles, candles[1:], strict=False):
        if current.open_time < previous.open_time:
            raise ValueError("future_candles must be sorted by open_time.")


def _find_entry_index(
    plan: TradePlan,
    candles: Sequence[Candle],
) -> int | None:
    for index, candle in enumerate(candles):
        if candle.low <= plan.entry_price <= candle.high:
            return index

    return None


def _resolve_barrier_hit(
    plan: TradePlan,
    candle: Candle,
) -> tuple[TradeOutcomeLabel, OutcomeExitReason, float] | None:
    if plan.direction == TradeDirection.LONG:
        stop_hit = candle.low <= plan.stop_loss
        take_profit_hit = candle.high >= plan.take_profit
    else:
        stop_hit = candle.high >= plan.stop_loss
        take_profit_hit = candle.low <= plan.take_profit

    if stop_hit:
        return (
            TradeOutcomeLabel.LOSS,
            OutcomeExitReason.STOP_LOSS_HIT,
            plan.stop_loss,
        )

    if take_profit_hit:
        return (
            TradeOutcomeLabel.WIN,
            OutcomeExitReason.TAKE_PROFIT_HIT,
            plan.take_profit,
        )

    return None


def _calculate_realized_r(plan: TradePlan, exit_price: float) -> float:
    if plan.direction == TradeDirection.LONG:
        profit_or_loss = exit_price - plan.entry_price
    else:
        profit_or_loss = plan.entry_price - exit_price

    return round(calculate_realized_r(profit_or_loss, plan.initial_risk), 4)


def _estimate_trade_costs(
    plan: TradePlan,
    exit_price: float,
    config: OutcomeConfig,
) -> TradeCostEstimate:
    entry_notional = plan.entry_price
    exit_notional = exit_price
    commission_amount = (
        (entry_notional + exit_notional) * config.commission_bps_per_side / 10_000
    )
    slippage_amount = (
        (entry_notional + exit_notional) * config.slippage_bps_per_side / 10_000
    )
    total_amount = commission_amount + slippage_amount
    return TradeCostEstimate(
        commission_amount=round(commission_amount, 8),
        slippage_amount=round(slippage_amount, 8),
        total_amount=round(total_amount, 8),
        cost_r=round(total_amount / plan.initial_risk, 4),
    )


def _calculate_excursion(
    plan: TradePlan,
    candles: Sequence[Candle],
) -> TradeExcursion:
    if plan.direction == TradeDirection.LONG:
        max_favorable_price = max(candle.high for candle in candles)
        max_adverse_price = min(candle.low for candle in candles)
        mfe_r = (max_favorable_price - plan.entry_price) / plan.initial_risk
        mae_r = (max_adverse_price - plan.entry_price) / plan.initial_risk
    else:
        max_favorable_price = min(candle.low for candle in candles)
        max_adverse_price = max(candle.high for candle in candles)
        mfe_r = (plan.entry_price - max_favorable_price) / plan.initial_risk
        mae_r = (plan.entry_price - max_adverse_price) / plan.initial_risk

    return TradeExcursion(
        mfe_r=round(mfe_r, 4),
        mae_r=round(mae_r, 4),
        max_favorable_price=max_favorable_price,
        max_adverse_price=max_adverse_price,
    )
