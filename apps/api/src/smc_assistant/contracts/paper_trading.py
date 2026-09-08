from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, PositiveFloat, field_validator


class StrictCamelModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, allow_inf_nan=False)

    @field_validator("*", mode="after")
    @classmethod
    def require_aware_datetime(cls, value: object) -> object:
        if isinstance(value, datetime) and value.utcoffset() is None:
            raise ValueError("Paper trade timestamps must be timezone-aware.")
        return value


class PaperTradeCreateRequest(StrictCamelModel):
    setup_id: str = Field(alias="setupId", min_length=8, max_length=200)
    account_balance: PositiveFloat = Field(alias="accountBalance")
    risk_percent: float = Field(alias="riskPercent", gt=0, le=100)


class PaperTradePriceRequest(StrictCamelModel):
    price: PositiveFloat
    occurred_at: datetime | None = Field(default=None, alias="occurredAt")


class PaperTradeCloseRequest(StrictCamelModel):
    exit_price: PositiveFloat = Field(alias="exitPrice")
    closed_at: datetime | None = Field(default=None, alias="closedAt")


class PaperTradeCancelRequest(StrictCamelModel):
    cancelled_at: datetime | None = Field(default=None, alias="cancelledAt")
