import csv
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from smc_assistant.application.market_data import MarketDataQuery
from smc_assistant.domain.candles import Candle


@dataclass(frozen=True, slots=True)
class CsvCandleColumns:
    open_time_candidates: tuple[str, ...] = ("open_time", "time", "timestamp")
    close_time: str = "close_time"
    open: str = "open"
    high: str = "high"
    low: str = "low"
    close: str = "close"
    volume: str = "volume"
    symbol: str = "symbol"
    timeframe: str = "timeframe"


class CsvMarketDataProvider:
    def __init__(
        self,
        path: str | Path,
        *,
        default_timeframe: str | None = None,
        columns: CsvCandleColumns | None = None,
    ) -> None:
        self._path = Path(path)
        self._default_timeframe = default_timeframe
        self._columns = columns or CsvCandleColumns()

    def load_candles(self, query: MarketDataQuery | None = None) -> tuple[Candle, ...]:
        market_data_query = query or MarketDataQuery()
        candles: list[Candle] = []

        with self._path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("CSV file must contain a header row.")

            for row_number, row in enumerate(reader, start=2):
                if not self._row_matches_query(row, market_data_query):
                    continue

                candle = self._candle_from_row(row, row_number, market_data_query)
                if not self._candle_matches_time_range(candle, market_data_query):
                    continue

                candles.append(candle)

        _ensure_chronological(candles)
        return tuple(candles)

    def _row_matches_query(
        self,
        row: Mapping[str, str],
        query: MarketDataQuery,
    ) -> bool:
        query_symbol = query.normalized_symbol
        if query_symbol is not None and self._columns.symbol in row:
            row_symbol = row[self._columns.symbol].strip().upper()
            if row_symbol != query_symbol:
                return False

        query_timeframe = query.timeframe
        if query_timeframe is not None and self._columns.timeframe in row:
            row_timeframe = row[self._columns.timeframe].strip()
            if row_timeframe != query_timeframe:
                return False

        return True

    def _candle_from_row(
        self,
        row: Mapping[str, str],
        row_number: int,
        query: MarketDataQuery,
    ) -> Candle:
        open_time = _parse_datetime(
            _get_first_value(row, self._columns.open_time_candidates, row_number),
            row_number,
            "open_time",
        )
        close_time_value = _get_optional_value(row, self._columns.close_time)
        if close_time_value is None:
            timeframe = query.timeframe or self._default_timeframe
            if timeframe is None:
                raise ValueError(
                    f"CSV row {row_number}: close_time is required when timeframe is unknown."
                )
            close_time = open_time + parse_timeframe_duration(timeframe)
        else:
            close_time = _parse_datetime(close_time_value, row_number, self._columns.close_time)

        volume_value = _get_optional_value(row, self._columns.volume)
        open_price = _parse_float(
            _get_required_value(row, self._columns.open, row_number),
            row_number,
            self._columns.open,
        )
        high = _parse_float(
            _get_required_value(row, self._columns.high, row_number),
            row_number,
            self._columns.high,
        )
        low = _parse_float(
            _get_required_value(row, self._columns.low, row_number),
            row_number,
            self._columns.low,
        )
        close = _parse_float(
            _get_required_value(row, self._columns.close, row_number),
            row_number,
            self._columns.close,
        )
        return Candle(
            open_time=open_time,
            close_time=close_time,
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=(
                None
                if volume_value is None
                else _parse_float(volume_value, row_number, self._columns.volume)
            ),
        )

    @staticmethod
    def _candle_matches_time_range(candle: Candle, query: MarketDataQuery) -> bool:
        if query.start_time is not None and candle.open_time < query.start_time:
            return False

        if query.end_time is not None and candle.open_time >= query.end_time:
            return False

        return True


def parse_timeframe_duration(timeframe: str) -> timedelta:
    normalized = timeframe.strip().upper()
    if normalized == "":
        raise ValueError("timeframe must not be empty.")

    if normalized.endswith("H"):
        return timedelta(hours=_parse_positive_int(normalized[:-1], timeframe))

    if normalized.endswith("D"):
        return timedelta(days=_parse_positive_int(normalized[:-1], timeframe))

    if normalized.endswith("M"):
        return timedelta(minutes=_parse_positive_int(normalized[:-1], timeframe))

    return timedelta(minutes=_parse_positive_int(normalized, timeframe))


def _ensure_chronological(candles: list[Candle]) -> None:
    for previous, current in zip(candles, candles[1:], strict=False):
        if current.open_time < previous.open_time:
            raise ValueError("CSV candles must be sorted by open_time.")


def _parse_positive_int(value: str, original_timeframe: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise ValueError(f"Unsupported timeframe: {original_timeframe}.") from error

    if parsed <= 0:
        raise ValueError("timeframe duration must be greater than zero.")

    return parsed


def _get_first_value(
    row: Mapping[str, str],
    candidates: tuple[str, ...],
    row_number: int,
) -> str:
    for candidate in candidates:
        value = _get_optional_value(row, candidate)
        if value is not None:
            return value

    raise ValueError(
        f"CSV row {row_number}: one of {', '.join(candidates)} columns is required."
    )


def _get_required_value(row: Mapping[str, str], column: str, row_number: int) -> str:
    value = _get_optional_value(row, column)
    if value is None:
        raise ValueError(f"CSV row {row_number}: {column} is required.")

    return value


def _get_optional_value(row: Mapping[str, str], column: str) -> str | None:
    value = row.get(column)
    if value is None or value.strip() == "":
        return None

    return value.strip()


def _parse_datetime(value: str, row_number: int, column: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"CSV row {row_number}: {column} must be an ISO datetime.") from error

    if parsed.tzinfo is None:
        raise ValueError(f"CSV row {row_number}: {column} must be timezone-aware.")

    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"CSV row {row_number}: {column} must be expressed in UTC.")

    return parsed.astimezone(UTC)


def _parse_float(value: str, row_number: int, column: str) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"CSV row {row_number}: {column} must be a number.") from error
