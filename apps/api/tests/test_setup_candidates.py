from dataclasses import replace
from datetime import UTC, datetime

from smc_assistant.application.setup_candidates import (
    setup_candidate_from_tradingview_payload,
)
from smc_assistant.application.setup_scoring import score_tradingview_payload
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.infrastructure.in_memory_setup_candidates import (
    InMemorySetupCandidateRepository,
)


def valid_payload() -> TradingViewWebhookPayload:
    return TradingViewWebhookPayload.model_validate(
        {
            "schemaVersion": "1.0",
            "eventId": "BTCUSDT-1-1767225660000-LONG",
            "eventType": "SETUP_CANDIDATE",
            "source": "TRADINGVIEW",
            "strategyVersion": "smc-rce-v1",
            "symbol": "BTCUSDT",
            "exchange": "BINANCE",
            "timeframe": "1",
            "barOpenTime": "2026-01-01T12:00:00Z",
            "barCloseTime": "2026-01-01T12:01:00Z",
            "direction": "LONG",
            "marketStructure": {
                "htfTimeframe": "15",
                "htfBias": "BULLISH",
                "bos": True,
                "choch": True,
                "liquiditySweep": True,
            },
            "fvg": {
                "lower": 65120.0,
                "upper": 65240.0,
                "equilibrium": 65180.0,
                "sizeAtrRatio": 0.42,
                "mitigationPercent": 0.0,
            },
            "execution": {
                "entry": 65180.0,
                "stopLoss": 64980.0,
                "takeProfit": 65580.0,
                "riskReward": 2.0,
            },
            "features": {
                "atr": None,
                "relativeVolume": None,
                "displacementScore": 0.81,
                "session": "NEW_YORK",
            },
        }
    )


def setup_candidate_record():
    payload = valid_payload()
    return setup_candidate_from_tradingview_payload(
        payload,
        score_tradingview_payload(payload),
        received_at=datetime(2026, 9, 3, 10, 0, tzinfo=UTC),
    )


def test_creates_setup_candidate_record_from_tradingview_payload_and_score() -> None:
    record = setup_candidate_record()

    assert record.setup_id == "BTCUSDT-1-1767225660000-LONG"
    assert record.event_id == "BTCUSDT-1-1767225660000-LONG"
    assert record.strategy_version == "smc-rce-v1"
    assert record.scoring_config_version == "rule-score-v1"
    assert record.symbol == "BTCUSDT"
    assert record.direction == "LONG"
    assert record.htf_bias == "BULLISH"
    assert record.score == 100.0
    assert record.accepted is True
    assert record.rejection_reasons == []
    assert len(record.components) == 7


def test_in_memory_setup_candidate_repository_is_idempotent_by_event_id() -> None:
    repository = InMemorySetupCandidateRepository()
    first_record = setup_candidate_record()
    second_record = setup_candidate_record()

    first_result = repository.save_if_absent(first_record)
    second_result = repository.save_if_absent(second_record)

    assert first_result.created is True
    assert second_result.created is False
    assert second_result.record == first_record
    assert repository.get_by_event_id(first_record.event_id) == first_record


def test_in_memory_setup_candidate_repository_lists_recent_records_with_filters() -> None:
    repository = InMemorySetupCandidateRepository()
    first_record = setup_candidate_record()
    second_record = replace(
        first_record,
        setup_id="ETHUSDT-1-1767225720000-LONG",
        event_id="ETHUSDT-1-1767225720000-LONG",
        symbol="ETHUSDT",
        received_at=datetime(2026, 9, 3, 10, 1, tzinfo=UTC),
    )
    rejected_record = replace(
        first_record,
        setup_id="SOLUSDT-1-1767225780000-LONG",
        event_id="SOLUSDT-1-1767225780000-LONG",
        symbol="SOLUSDT",
        accepted=False,
        received_at=datetime(2026, 9, 3, 10, 2, tzinfo=UTC),
    )

    repository.save_if_absent(first_record)
    repository.save_if_absent(second_record)
    repository.save_if_absent(rejected_record)

    assert [record.symbol for record in repository.list_recent(limit=2)] == [
        "SOLUSDT",
        "ETHUSDT",
    ]
    assert [record.symbol for record in repository.list_recent(symbol="ETHUSDT")] == [
        "ETHUSDT"
    ]
    assert [record.symbol for record in repository.list_recent(accepted=False)] == [
        "SOLUSDT"
    ]


def test_in_memory_setup_candidate_repository_gets_by_setup_id() -> None:
    repository = InMemorySetupCandidateRepository()
    record = setup_candidate_record()
    repository.save_if_absent(record)

    assert repository.get_by_setup_id(record.setup_id) == record
    assert repository.get_by_setup_id("missing-setup") is None
