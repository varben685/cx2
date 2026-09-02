from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, field_validator, model_validator

from smc_assistant.domain.enums import TradeDirection


class WebhookEventType(StrEnum):
    SETUP_CANDIDATE = "SETUP_CANDIDATE"


class WebhookSource(StrEnum):
    TRADINGVIEW = "TRADINGVIEW"


class MarketBiasValue(StrEnum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class TradingSession(StrEnum):
    ASIA = "ASIA"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    OFF_HOURS = "OFF_HOURS"


class StrictCamelModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MarketStructurePayload(StrictCamelModel):
    htf_timeframe: str = Field(alias="htfTimeframe", min_length=1)
    htf_bias: MarketBiasValue = Field(alias="htfBias")
    bos: bool
    choch: bool
    liquidity_sweep: bool = Field(alias="liquiditySweep")

    @field_validator("htf_timeframe")
    @classmethod
    def validate_htf_timeframe(cls, value: str) -> str:
        return validate_timeframe(value)


class FairValueGapPayload(StrictCamelModel):
    lower: PositiveFloat
    upper: PositiveFloat
    equilibrium: PositiveFloat
    size_atr_ratio: float = Field(alias="sizeAtrRatio", ge=0)
    mitigation_percent: float = Field(alias="mitigationPercent", ge=0, le=100)

    @model_validator(mode="after")
    def validate_price_order(self) -> "FairValueGapPayload":
        if self.lower >= self.upper:
            raise ValueError("fvg.lower must be less than fvg.upper.")

        if not self.lower <= self.equilibrium <= self.upper:
            raise ValueError("fvg.equilibrium must be between lower and upper.")

        return self


class ExecutionPayload(StrictCamelModel):
    entry: PositiveFloat
    stop_loss: PositiveFloat = Field(alias="stopLoss")
    take_profit: PositiveFloat = Field(alias="takeProfit")
    risk_reward: PositiveFloat = Field(alias="riskReward")


class FeaturePayload(StrictCamelModel):
    atr: PositiveFloat | None = None
    relative_volume: float | None = Field(default=None, alias="relativeVolume", ge=0)
    displacement_score: float = Field(alias="displacementScore", ge=0, le=1)
    session: TradingSession


class TradingViewWebhookPayload(StrictCamelModel):
    schema_version: Literal["1.0"] = Field(alias="schemaVersion")
    event_id: Annotated[str, Field(alias="eventId", min_length=8, max_length=200)]
    event_type: WebhookEventType = Field(alias="eventType")
    source: WebhookSource
    strategy_version: Annotated[str, Field(alias="strategyVersion", min_length=1, max_length=80)]
    symbol: Annotated[str, Field(min_length=1, max_length=40)]
    exchange: Annotated[str, Field(min_length=1, max_length=40)]
    timeframe: str
    bar_open_time: datetime = Field(alias="barOpenTime")
    bar_close_time: datetime = Field(alias="barCloseTime")
    direction: TradeDirection
    market_structure: MarketStructurePayload = Field(alias="marketStructure")
    fvg: FairValueGapPayload
    execution: ExecutionPayload
    features: FeaturePayload

    @field_validator("timeframe")
    @classmethod
    def validate_payload_timeframe(cls, value: str) -> str:
        return validate_timeframe(value)

    @field_validator("bar_open_time", "bar_close_time")
    @classmethod
    def require_timezone_aware_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("bar timestamps must be timezone-aware.")

        return value

    @model_validator(mode="after")
    def validate_temporal_and_execution_consistency(self) -> "TradingViewWebhookPayload":
        if self.bar_close_time <= self.bar_open_time:
            raise ValueError("barCloseTime must be after barOpenTime.")

        if self.direction == TradeDirection.LONG:
            if not self.stop_loss < self.entry < self.take_profit:
                raise ValueError("LONG execution requires stopLoss < entry < takeProfit.")

        if self.direction == TradeDirection.SHORT:
            if not self.take_profit < self.entry < self.stop_loss:
                raise ValueError("SHORT execution requires takeProfit < entry < stopLoss.")

        expected_risk_reward = abs(self.take_profit - self.entry) / abs(self.entry - self.stop_loss)
        if abs(self.execution.risk_reward - expected_risk_reward) > 0.01:
            raise ValueError("riskReward must match entry, stopLoss and takeProfit.")

        return self

    @property
    def entry(self) -> float:
        return self.execution.entry

    @property
    def stop_loss(self) -> float:
        return self.execution.stop_loss

    @property
    def take_profit(self) -> float:
        return self.execution.take_profit


def validate_timeframe(value: str) -> str:
    normalized = value.strip().upper()
    if not normalized:
        raise ValueError("timeframe must not be empty.")

    if normalized.isdigit() and int(normalized) > 0:
        return normalized

    if normalized in {"D", "W", "M"}:
        return normalized

    raise ValueError("timeframe must be a positive minute value or one of D, W, M.")
