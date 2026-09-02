from datetime import UTC, datetime, timedelta, timezone

import pytest

from smc_assistant.domain.candles import Candle


def make_candle(
    index: int,
    *,
    open_price: float = 100.0,
    high: float = 105.0,
    low: float = 95.0,
    close: float = 101.0,
) -> Candle:
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC) + timedelta(minutes=index)
    return Candle(
        open_time=open_time,
        close_time=open_time + timedelta(minutes=1),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=1000.0,
    )


def test_candle_accepts_valid_ohlcv_data() -> None:
    candle = make_candle(0)

    assert candle.open == 100.0
    assert candle.high == 105.0
    assert candle.low == 95.0
    assert candle.close == 101.0
    assert candle.volume == 1000.0


def test_candle_rejects_non_utc_time() -> None:
    with pytest.raises(ValueError, match="UTC"):
        Candle(
            open_time=datetime(2026, 1, 1, 13, 0, tzinfo=timezone(timedelta(hours=1))),
            close_time=datetime(2026, 1, 1, 13, 1, tzinfo=timezone(timedelta(hours=1))),
            open=100.0,
            high=105.0,
            low=95.0,
            close=101.0,
        )


def test_candle_rejects_invalid_ohlc_relationships() -> None:
    with pytest.raises(ValueError, match="high"):
        make_candle(0, open_price=100.0, high=99.0, low=95.0, close=101.0)


def test_candle_rejects_negative_volume() -> None:
    open_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="volume"):
        Candle(
            open_time=open_time,
            close_time=open_time + timedelta(minutes=1),
            open=100.0,
            high=105.0,
            low=95.0,
            close=101.0,
            volume=-1.0,
        )
