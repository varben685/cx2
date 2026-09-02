from datetime import UTC, datetime, timedelta

from smc_assistant.domain.candles import Candle


def build_phase1_synthetic_candles() -> list[Candle]:
    """Return a small deterministic OHLCV set for Phase 1 domain examples."""
    rows = [
        (98.0, 100.0, 95.0, 99.0, 100.0),
        (99.0, 105.0, 96.0, 104.0, 100.0),
        (103.0, 103.0, 94.0, 95.0, 100.0),
        (98.0, 107.0, 97.0, 106.0, 100.0),
        (100.0, 104.0, 93.0, 93.5, 100.0),
        (108.0, 118.0, 108.0, 117.0, 200.0),
        (95.0, 100.0, 92.0, 96.0, 120.0),
        (104.0, 105.0, 95.0, 96.0, 120.0),
    ]
    start_time = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

    return [
        Candle(
            open_time=start_time + timedelta(minutes=index),
            close_time=start_time + timedelta(minutes=index + 1),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        for index, (open_price, high, low, close, volume) in enumerate(rows)
    ]
