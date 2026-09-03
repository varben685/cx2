from copy import deepcopy
from datetime import UTC, datetime, timedelta

from smc_assistant.application.audit import AuditEvent, AuditEventType
from smc_assistant.application.webhook_ingestion import (
    WebhookIngestionService,
    WebhookIngestionStatus,
)
from smc_assistant.contracts.tradingview import TradingViewWebhookPayload
from smc_assistant.infrastructure.in_memory_webhook_events import (
    InMemoryWebhookEventRepository,
)


class RecordingAuditLogger:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)


def valid_payload() -> TradingViewWebhookPayload:
    return TradingViewWebhookPayload.model_validate(
        {
            "schemaVersion": "1.0",
            "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
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
                "bos": False,
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
                "takeProfit": 65780.0,
                "riskReward": 3.0,
            },
            "features": {
                "atr": 285.0,
                "relativeVolume": 1.7,
                "displacementScore": 0.81,
                "session": "NEW_YORK",
            },
        }
    )


def test_ingestion_accepts_new_webhook_event() -> None:
    repository = InMemoryWebhookEventRepository()
    audit_logger = RecordingAuditLogger()
    service = WebhookIngestionService(repository, audit_logger)
    received_at = datetime(2026, 9, 3, 10, 0, tzinfo=UTC)

    result = service.ingest_tradingview(valid_payload(), received_at=received_at)

    assert result.status == WebhookIngestionStatus.ACCEPTED
    assert result.event_id == "BTCUSDT-1m-1720000000-bullish-choch"
    assert result.received_at == received_at
    assert result.first_received_at == received_at
    assert result.setup_score.accepted is True
    assert result.setup_score.score == 100.0
    assert repository.get_by_event_id(result.event_id) is not None
    assert audit_logger.events[0].event_type == AuditEventType.WEBHOOK_ACCEPTED
    assert audit_logger.events[0].metadata["event_id"] == result.event_id
    assert audit_logger.events[0].metadata["setup_score"] == 100.0
    assert audit_logger.events[0].metadata["setup_accepted"] is True
    assert audit_logger.events[0].metadata["scoring_config_version"] == "rule-score-v1"
    assert "payload" not in audit_logger.events[0].metadata


def test_ingestion_marks_repeated_event_id_as_duplicate() -> None:
    audit_logger = RecordingAuditLogger()
    service = WebhookIngestionService(InMemoryWebhookEventRepository(), audit_logger)
    first_received_at = datetime(2026, 9, 3, 10, 0, tzinfo=UTC)
    second_received_at = first_received_at + timedelta(seconds=30)

    first_result = service.ingest_tradingview(
        valid_payload(),
        received_at=first_received_at,
    )
    second_result = service.ingest_tradingview(
        valid_payload(),
        received_at=second_received_at,
    )

    assert first_result.status == WebhookIngestionStatus.ACCEPTED
    assert second_result.status == WebhookIngestionStatus.DUPLICATE
    assert second_result.received_at == second_received_at
    assert second_result.first_received_at == first_received_at
    assert second_result.setup_score.score == first_result.setup_score.score
    assert audit_logger.events[1].event_type == AuditEventType.WEBHOOK_DUPLICATE
    assert audit_logger.events[1].metadata["event_id"] == second_result.event_id
    assert audit_logger.events[1].metadata["first_received_at"] == first_received_at.isoformat()
    assert audit_logger.events[1].metadata["setup_score"] == 100.0
    assert "payload" not in audit_logger.events[1].metadata


def test_ingestion_uses_first_payload_for_duplicate_event_id() -> None:
    repository = InMemoryWebhookEventRepository()
    service = WebhookIngestionService(repository)
    first_payload = valid_payload()
    second_payload_data = deepcopy(first_payload.model_dump(mode="json", by_alias=True))
    second_payload_data["symbol"] = "ETHUSDT"
    second_payload = TradingViewWebhookPayload.model_validate(second_payload_data)

    service.ingest_tradingview(first_payload)
    duplicate_result = service.ingest_tradingview(second_payload)
    stored_record = repository.get_by_event_id(first_payload.event_id)

    assert duplicate_result.status == WebhookIngestionStatus.DUPLICATE
    assert stored_record is not None
    assert stored_record.payload["symbol"] == "BTCUSDT"
