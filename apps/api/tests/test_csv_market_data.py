from datetime import UTC, datetime

import pytest

from smc_assistant.application.market_data import MarketDataProvider, MarketDataQuery
from smc_assistant.infrastructure.csv_market_data import (
    CsvMarketDataProvider,
    parse_timeframe_duration,
)


def test_csv_market_data_provider_imports_ohlcv_with_inferred_close_time(tmp_path) -> None:
    csv_path = tmp_path / "btc.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close,volume",
                "2026-01-01T12:00:00Z,100,105,99,104,1200",
                "2026-01-01T12:01:00Z,104,106,103,105,1300",
            ]
        ),
        encoding="utf-8",
    )
    provider: MarketDataProvider = CsvMarketDataProvider(csv_path, default_timeframe="1")

    candles = provider.load_candles()

    assert len(candles) == 2
    assert candles[0].open_time == datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert candles[0].close_time == datetime(2026, 1, 1, 12, 1, tzinfo=UTC)
    assert candles[0].open == 100.0
    assert candles[0].high == 105.0
    assert candles[0].low == 99.0
    assert candles[0].close == 104.0
    assert candles[0].volume == 1200.0


def test_csv_market_data_provider_filters_by_symbol_timeframe_and_time_range(tmp_path) -> None:
    csv_path = tmp_path / "multi.csv"
    csv_path.write_text(
        "\n".join(
            [
                "symbol,timeframe,open_time,close_time,open,high,low,close,volume",
                "BTCUSDT,1,2026-01-01T12:00:00Z,2026-01-01T12:01:00Z,100,105,99,104,1200",
                "ETHUSDT,1,2026-01-01T12:01:00Z,2026-01-01T12:02:00Z,200,205,199,204,2200",
                "BTCUSDT,5,2026-01-01T12:02:00Z,2026-01-01T12:07:00Z,101,106,100,105,1300",
                "BTCUSDT,1,2026-01-01T12:03:00Z,2026-01-01T12:04:00Z,102,107,101,106,1400",
            ]
        ),
        encoding="utf-8",
    )
    provider = CsvMarketDataProvider(csv_path)

    candles = provider.load_candles(
        MarketDataQuery(
            symbol="btcusdt",
            timeframe="1",
            start_time=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
            end_time=datetime(2026, 1, 1, 12, 4, tzinfo=UTC),
        )
    )

    assert len(candles) == 1
    assert candles[0].open_time == datetime(2026, 1, 1, 12, 3, tzinfo=UTC)
    assert candles[0].close == 106.0


def test_csv_market_data_provider_rejects_missing_close_time_without_timeframe(tmp_path) -> None:
    csv_path = tmp_path / "missing-close-time.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close",
                "2026-01-01T12:00:00Z,100,105,99,104",
            ]
        ),
        encoding="utf-8",
    )
    provider = CsvMarketDataProvider(csv_path)

    with pytest.raises(ValueError, match="close_time is required"):
        provider.load_candles()


def test_csv_market_data_provider_rejects_non_utc_timestamps(tmp_path) -> None:
    csv_path = tmp_path / "non-utc.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close",
                "2026-01-01T13:00:00+01:00,100,105,99,104",
            ]
        ),
        encoding="utf-8",
    )
    provider = CsvMarketDataProvider(csv_path, default_timeframe="1")

    with pytest.raises(ValueError, match="must be expressed in UTC"):
        provider.load_candles()


def test_csv_market_data_provider_rejects_unsorted_candles(tmp_path) -> None:
    csv_path = tmp_path / "unsorted.csv"
    csv_path.write_text(
        "\n".join(
            [
                "time,open,high,low,close",
                "2026-01-01T12:01:00Z,100,105,99,104",
                "2026-01-01T12:00:00Z,100,105,99,104",
            ]
        ),
        encoding="utf-8",
    )
    provider = CsvMarketDataProvider(csv_path, default_timeframe="1")

    with pytest.raises(ValueError, match="sorted by open_time"):
        provider.load_candles()


def test_market_data_query_validates_utc_time_range() -> None:
    with pytest.raises(ValueError, match="end_time must be after start_time"):
        MarketDataQuery(
            start_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            end_time=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    ("timeframe", "seconds"),
    [
        ("1", 60),
        ("15m", 900),
        ("1H", 3600),
        ("1D", 86400),
    ],
)
def test_parse_timeframe_duration(timeframe: str, seconds: int) -> None:
    assert parse_timeframe_duration(timeframe).total_seconds() == seconds
