from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload


class BacktestConfig(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        alias_generator=to_camel,
        allow_inf_nan=False,
        from_attributes=True,
    )

    max_holding_bars: int = Field(default=30, ge=1, le=5000)
    entry_timeout_bars: int = Field(default=5, ge=1, le=5000)
    commission_bps_per_side: float = Field(default=0, ge=0, le=10000)
    slippage_bps_per_side: float = Field(default=0, ge=0, le=10000)


class BacktestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_camel)

    run_id: UUID
    setups: list[TradingViewWebhookPayload] = Field(min_length=1, max_length=25)
    candles_csv: str = Field(min_length=1, max_length=1_000_000)
    config: BacktestConfig = Field(default_factory=BacktestConfig)

    @model_validator(mode="after")
    def validate_setup_batch(self) -> "BacktestRequest":
        if len({setup.event_id for setup in self.setups}) != len(self.setups):
            raise ValueError("Setup event IDs must be unique within a backtest.")
        markets = {
            (setup.symbol, setup.exchange, setup.timeframe, setup.strategy_version)
            for setup in self.setups
        }
        if len(markets) != 1:
            raise ValueError("A backtest must use one symbol, exchange, timeframe and strategy.")
        timeframe = self.setups[0].timeframe
        if timeframe.isdigit() and int(timeframe) > 10080:
            raise ValueError("Minute timeframe must not exceed 10080.")
        return self
