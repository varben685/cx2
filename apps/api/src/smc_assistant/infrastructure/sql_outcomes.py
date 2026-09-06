from typing import Any
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.outcome_records import OutcomeRecord, OutcomeSaveResult
from smc_assistant.infrastructure.webhook_event_schema import outcome_records

_record_adapter = TypeAdapter(OutcomeRecord)


def outcome_record_values(record: OutcomeRecord) -> dict[str, Any]:
    return {
        "outcome_id": record.outcome_id,
        "run_id": record.run_id,
        "event_id": record.evaluation.event_id,
        "symbol": record.evaluation.symbol,
        "label": record.evaluation.outcome.label.value,
        "evaluated_at": record.evaluated_at,
        "snapshot": _record_adapter.dump_python(record, mode="json"),
    }


class SQLOutcomeRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save_if_absent(self, record: OutcomeRecord) -> OutcomeSaveResult:
        existing = self.get_by_run_event(record.run_id, record.evaluation.event_id)
        if existing is not None:
            return OutcomeSaveResult(record=existing, created=False)
        try:
            with self._engine.begin() as connection:
                connection.execute(insert(outcome_records).values(**outcome_record_values(record)))
        except IntegrityError:
            existing = self.get_by_run_event(record.run_id, record.evaluation.event_id)
            if existing is None:
                raise
            return OutcomeSaveResult(record=existing, created=False)
        return OutcomeSaveResult(record=record, created=True)

    def get_by_outcome_id(self, outcome_id: UUID) -> OutcomeRecord | None:
        query = select(outcome_records.c.snapshot).where(outcome_records.c.outcome_id == outcome_id)
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _record_adapter.validate_python(snapshot) if snapshot is not None else None

    def get_by_run_event(self, run_id: UUID, event_id: str) -> OutcomeRecord | None:
        query = select(outcome_records.c.snapshot).where(
            outcome_records.c.run_id == run_id,
            outcome_records.c.event_id == event_id,
        )
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _record_adapter.validate_python(snapshot) if snapshot is not None else None

    def list_recent(
        self,
        *,
        limit: int = 50,
        run_id: UUID | None = None,
        event_id: str | None = None,
        symbol: str | None = None,
    ) -> list[OutcomeRecord]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        query = select(outcome_records.c.snapshot)
        if run_id is not None:
            query = query.where(outcome_records.c.run_id == run_id)
        if event_id is not None:
            query = query.where(outcome_records.c.event_id == event_id)
        if symbol is not None:
            query = query.where(outcome_records.c.symbol == symbol)
        query = query.order_by(
            outcome_records.c.evaluated_at.desc(), outcome_records.c.outcome_id.desc()
        ).limit(limit)
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_record_adapter.validate_python(snapshot) for snapshot in snapshots]

    def list_for_run(self, run_id: UUID, *, symbol: str | None = None) -> list[OutcomeRecord]:
        query = select(outcome_records.c.snapshot).where(outcome_records.c.run_id == run_id)
        if symbol is not None:
            query = query.where(outcome_records.c.symbol == symbol)
        query = query.order_by(outcome_records.c.outcome_id)
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_record_adapter.validate_python(snapshot) for snapshot in snapshots]
