from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Engine, Select, insert, select
from sqlalchemy.engine import RowMapping
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.setup_candidates import (
    SetupCandidateRecord,
    SetupCandidateSaveResult,
)
from smc_assistant.infrastructure.webhook_event_schema import setup_candidates


class SQLSetupCandidateRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_if_absent(self, record: SetupCandidateRecord) -> SetupCandidateSaveResult:
        existing_record = self.get_by_event_id(record.event_id)
        if existing_record is not None:
            return SetupCandidateSaveResult(record=existing_record, created=False)

        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(setup_candidates).values(
                        setup_id=record.setup_id,
                        event_id=record.event_id,
                        schema_version=record.schema_version,
                        strategy_version=record.strategy_version,
                        scoring_config_version=record.scoring_config_version,
                        symbol=record.symbol,
                        exchange=record.exchange,
                        timeframe=record.timeframe,
                        direction=record.direction,
                        htf_bias=record.htf_bias,
                        score=record.score,
                        accepted=record.accepted,
                        components=record.components,
                        rejection_reasons=record.rejection_reasons,
                        positive_reasons=record.positive_reasons,
                        negative_reasons=record.negative_reasons,
                        bar_close_time=record.bar_close_time,
                        received_at=record.received_at,
                        created_at=datetime.now(UTC),
                    )
                )
        except IntegrityError:
            duplicated_record = self.get_by_event_id(record.event_id)
            if duplicated_record is None:
                raise
            return SetupCandidateSaveResult(record=duplicated_record, created=False)

        return SetupCandidateSaveResult(record=record, created=True)

    def get_by_event_id(self, event_id: str) -> SetupCandidateRecord | None:
        query = _select_setup_candidate_records().where(setup_candidates.c.event_id == event_id)

        with self._engine.connect() as connection:
            row = connection.execute(query).mappings().one_or_none()

        if row is None:
            return None

        return _record_from_row(row)

    def get_by_setup_id(self, setup_id: str) -> SetupCandidateRecord | None:
        query = _select_setup_candidate_records().where(setup_candidates.c.setup_id == setup_id)

        with self._engine.connect() as connection:
            row = connection.execute(query).mappings().one_or_none()

        if row is None:
            return None

        return _record_from_row(row)

    def list_recent(
        self,
        *,
        limit: int = 50,
        symbol: str | None = None,
        accepted: bool | None = None,
    ) -> list[SetupCandidateRecord]:
        query = _select_setup_candidate_records()

        if symbol is not None:
            query = query.where(setup_candidates.c.symbol == symbol)

        if accepted is not None:
            query = query.where(setup_candidates.c.accepted.is_(accepted))

        query = query.order_by(
            setup_candidates.c.received_at.desc(),
            setup_candidates.c.setup_id.desc(),
        ).limit(limit)

        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()

        return [_record_from_row(row) for row in rows]


def _select_setup_candidate_records() -> Select[Any]:
    return select(
        setup_candidates.c.setup_id,
        setup_candidates.c.event_id,
        setup_candidates.c.schema_version,
        setup_candidates.c.strategy_version,
        setup_candidates.c.scoring_config_version,
        setup_candidates.c.symbol,
        setup_candidates.c.exchange,
        setup_candidates.c.timeframe,
        setup_candidates.c.direction,
        setup_candidates.c.htf_bias,
        setup_candidates.c.score,
        setup_candidates.c.accepted,
        setup_candidates.c.components,
        setup_candidates.c.rejection_reasons,
        setup_candidates.c.positive_reasons,
        setup_candidates.c.negative_reasons,
        setup_candidates.c.bar_close_time,
        setup_candidates.c.received_at,
    )


def _record_from_row(row: RowMapping) -> SetupCandidateRecord:
    return SetupCandidateRecord(
        setup_id=str(row["setup_id"]),
        event_id=str(row["event_id"]),
        schema_version=str(row["schema_version"]),
        strategy_version=str(row["strategy_version"]),
        scoring_config_version=str(row["scoring_config_version"]),
        symbol=str(row["symbol"]),
        exchange=str(row["exchange"]),
        timeframe=str(row["timeframe"]),
        direction=str(row["direction"]),
        htf_bias=str(row["htf_bias"]),
        score=float(row["score"]),
        accepted=bool(row["accepted"]),
        components=_json_list(row["components"]),
        rejection_reasons=_string_list(row["rejection_reasons"]),
        positive_reasons=_string_list(row["positive_reasons"]),
        negative_reasons=_string_list(row["negative_reasons"]),
        bar_close_time=_datetime_from_row(row, "bar_close_time"),
        received_at=_datetime_from_row(row, "received_at"),
    )


def _datetime_from_row(row: RowMapping, key: str) -> datetime:
    value = row[key]
    if not isinstance(value, datetime):
        msg = f"setup_candidates.{key} must be a datetime"
        raise TypeError(msg)

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value


def _json_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        msg = "setup_candidates.components must be a list"
        raise TypeError(msg)

    return [dict(item) for item in value]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        msg = "setup candidate reason fields must be lists"
        raise TypeError(msg)

    return [str(item) for item in value]
