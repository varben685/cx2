from threading import Lock
from uuid import UUID

from smc_assistant.application.paper_trading import (
    PaperTradeAlreadyExistsError,
    PaperTradeNotFoundError,
    PaperTradeRevisionConflictError,
)
from smc_assistant.domain.paper_trading import PaperTrade, PaperTradeEvent, PaperTradeStatus


class InMemoryPaperTradeRepository:
    def __init__(self) -> None:
        self._trades: dict[UUID, PaperTrade] = {}
        self._trade_ids_by_setup: dict[str, UUID] = {}
        self._events: dict[UUID, list[PaperTradeEvent]] = {}
        self._lock = Lock()

    def create(self, trade: PaperTrade, event: PaperTradeEvent) -> PaperTrade:
        with self._lock:
            if trade.setup_id in self._trade_ids_by_setup or trade.trade_id in self._trades:
                raise PaperTradeAlreadyExistsError("A paper trade already exists for this setup.")
            self._trades[trade.trade_id] = trade
            self._trade_ids_by_setup[trade.setup_id] = trade.trade_id
            self._events[trade.trade_id] = [event]
        return trade

    def get(self, trade_id: UUID) -> PaperTrade | None:
        with self._lock:
            return self._trades.get(trade_id)

    def get_by_setup_id(self, setup_id: str) -> PaperTrade | None:
        with self._lock:
            trade_id = self._trade_ids_by_setup.get(setup_id)
            return self._trades.get(trade_id) if trade_id is not None else None

    def list_recent(
        self,
        *,
        limit: int = 100,
        status: PaperTradeStatus | None = None,
        symbol: str | None = None,
    ) -> list[PaperTrade]:
        if limit < 1:
            raise ValueError("limit must be greater than zero.")
        with self._lock:
            trades = list(self._trades.values())
        return sorted(
            (
                trade
                for trade in trades
                if (status is None or trade.status == status)
                and (symbol is None or trade.symbol == symbol)
            ),
            key=lambda trade: (trade.updated_at, trade.trade_id),
            reverse=True,
        )[:limit]

    def list_all(self) -> list[PaperTrade]:
        with self._lock:
            return list(self._trades.values())

    def update(
        self,
        trade: PaperTrade,
        event: PaperTradeEvent,
        *,
        expected_revision: int,
    ) -> PaperTrade:
        with self._lock:
            current = self._trades.get(trade.trade_id)
            if current is None:
                raise PaperTradeNotFoundError("Paper trade not found.")
            if current.revision != expected_revision:
                raise PaperTradeRevisionConflictError(
                    "Paper trade was modified by another request."
                )
            if trade.revision != expected_revision + 1 or event.sequence != trade.revision:
                raise ValueError("Paper trade revision and event sequence must increment by one.")
            self._trades[trade.trade_id] = trade
            self._events[trade.trade_id].append(event)
        return trade

    def list_events(self, trade_id: UUID) -> list[PaperTradeEvent]:
        with self._lock:
            return list(self._events.get(trade_id, []))
