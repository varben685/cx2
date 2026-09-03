from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.domain.setup_scoring import SetupScore


@dataclass(frozen=True, slots=True)
class SetupCandidateRecord:
    setup_id: str
    event_id: str
    schema_version: str
    strategy_version: str
    scoring_config_version: str
    symbol: str
    exchange: str
    timeframe: str
    direction: str
    htf_bias: str
    score: float
    accepted: bool
    components: list[dict[str, Any]]
    rejection_reasons: list[str]
    positive_reasons: list[str]
    negative_reasons: list[str]
    bar_close_time: datetime
    received_at: datetime


@dataclass(frozen=True, slots=True)
class SetupCandidateSaveResult:
    record: SetupCandidateRecord
    created: bool


class SetupCandidateRepository(Protocol):
    def save_if_absent(self, record: SetupCandidateRecord) -> SetupCandidateSaveResult:
        pass

    def get_by_event_id(self, event_id: str) -> SetupCandidateRecord | None:
        pass


def setup_candidate_from_tradingview_payload(
    payload: TradingViewWebhookPayload,
    setup_score: SetupScore,
    *,
    received_at: datetime,
) -> SetupCandidateRecord:
    return SetupCandidateRecord(
        setup_id=payload.event_id,
        event_id=payload.event_id,
        schema_version=payload.schema_version,
        strategy_version=setup_score.strategy_version,
        scoring_config_version=setup_score.config_version,
        symbol=payload.symbol,
        exchange=payload.exchange,
        timeframe=payload.timeframe,
        direction=payload.direction.value,
        htf_bias=payload.market_structure.htf_bias.value,
        score=setup_score.score,
        accepted=setup_score.accepted,
        components=[
            {
                "name": component.name.value,
                "score": component.score,
                "maxScore": component.max_score,
                "reason": component.reason,
            }
            for component in setup_score.components
        ],
        rejection_reasons=[reason.value for reason in setup_score.rejection_reasons],
        positive_reasons=list(setup_score.positive_reasons),
        negative_reasons=list(setup_score.negative_reasons),
        bar_close_time=payload.bar_close_time,
        received_at=received_at,
    )
