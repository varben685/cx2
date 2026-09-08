from typing import Any, cast
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import Engine, insert, select, update
from sqlalchemy.exc import IntegrityError

from smc_assistant.application.paper_trading import (
    PaperTradeAlreadyExistsError,
    PaperTradeNotFoundError,
    PaperTradeRevisionConflictError,
)
from smc_assistant.domain.paper_trading import PaperTrade, PaperTradeEvent, PaperTradeStatus
from smc_assistant.infrastructure.webhook_event_schema import paper_trade_events, paper_trades

_trade_adapter = TypeAdapter(PaperTrade)
_event_adapter = TypeAdapter(PaperTradeEvent)


def _trade_snapshot(value: PaperTrade) -> dict[str, Any]:
    return cast(dict[str, Any], _trade_adapter.dump_python(value, mode="json"))


def _event_snapshot(value: PaperTradeEvent) -> dict[str, Any]:
    return cast(dict[str, Any], _event_adapter.dump_python(value, mode="json"))


def _trade_values(trade: PaperTrade) -> dict[str, Any]:
    return {
        "trade_id": trade.trade_id,
        "setup_id": trade.setup_id,
        "symbol": trade.symbol,
        "status": trade.status.value,
        "opened_at": trade.opened_at,
        "closed_at": trade.closed_at,
        "updated_at": trade.updated_at,
        "revision": trade.revision,
        "snapshot": _trade_snapshot(trade),
    }


def _event_values(event: PaperTradeEvent) -> dict[str, Any]:
    return {
        "trade_id": event.trade_id,
        "sequence": event.sequence,
        "event_type": event.event_type.value,
        "occurred_at": event.occurred_at,
        "snapshot": _event_snapshot(event),
    }


class SQLPaperTradeRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, trade: PaperTrade, event: PaperTradeEvent) -> PaperTrade:
        try:
            with self._engine.begin() as connection:
                connection.execute(insert(paper_trades).values(**_trade_values(trade)))
                connection.execute(insert(paper_trade_events).values(**_event_values(event)))
        except IntegrityError as error:
            if self.get_by_setup_id(trade.setup_id) is not None:
                raise PaperTradeAlreadyExistsError(
                    "A paper trade already exists for this setup."
                ) from error
            raise
        return trade

    def get(self, trade_id: UUID) -> PaperTrade | None:
        query = select(paper_trades.c.snapshot).where(paper_trades.c.trade_id == trade_id)
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _trade_adapter.validate_python(snapshot) if snapshot is not None else None

    def get_by_setup_id(self, setup_id: str) -> PaperTrade | None:
        query = select(paper_trades.c.snapshot).where(paper_trades.c.setup_id == setup_id)
        with self._engine.connect() as connection:
            snapshot = connection.execute(query).scalar_one_or_none()
        return _trade_adapter.validate_python(snapshot) if snapshot is not None else None

    def list_recent(
        self,
        *,
        limit: int = 100,
        status: PaperTradeStatus | None = None,
        symbol: str | None = None,
    ) -> list[PaperTrade]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        query = select(paper_trades.c.snapshot)
        if status is not None:
            query = query.where(paper_trades.c.status == status.value)
        if symbol is not None:
            query = query.where(paper_trades.c.symbol == symbol)
        query = query.order_by(
            paper_trades.c.updated_at.desc(), paper_trades.c.trade_id.desc()
        ).limit(limit)
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_trade_adapter.validate_python(snapshot) for snapshot in snapshots]

    def list_all(self) -> list[PaperTrade]:
        query = select(paper_trades.c.snapshot)
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_trade_adapter.validate_python(snapshot) for snapshot in snapshots]

    def update(
        self,
        trade: PaperTrade,
        event: PaperTradeEvent,
        *,
        expected_revision: int,
    ) -> PaperTrade:
        if trade.revision != expected_revision + 1 or event.sequence != trade.revision:
            raise ValueError("Paper trade revision and event sequence must increment by one.")
        with self._engine.begin() as connection:
            current_revision = connection.execute(
                select(paper_trades.c.revision)
                .where(paper_trades.c.trade_id == trade.trade_id)
                .with_for_update()
            ).scalar_one_or_none()
            if current_revision is None:
                raise PaperTradeNotFoundError("Paper trade not found.")
            if current_revision != expected_revision:
                raise PaperTradeRevisionConflictError(
                    "Paper trade was modified by another request."
                )
            connection.execute(
                update(paper_trades)
                .where(paper_trades.c.trade_id == trade.trade_id)
                .values(**_trade_values(trade))
            )
            connection.execute(insert(paper_trade_events).values(**_event_values(event)))
        return trade

    def list_events(self, trade_id: UUID) -> list[PaperTradeEvent]:
        query = (
            select(paper_trade_events.c.snapshot)
            .where(paper_trade_events.c.trade_id == trade_id)
            .order_by(paper_trade_events.c.sequence)
        )
        with self._engine.connect() as connection:
            snapshots = connection.execute(query).scalars().all()
        return [_event_adapter.validate_python(snapshot) for snapshot in snapshots]
