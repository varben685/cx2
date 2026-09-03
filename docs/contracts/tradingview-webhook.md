# TradingView webhook contract

Az első verzió célja egy verziózott JSON payload, amely Pydantic modellel
validálható és JSON Schema formában is exportálható.

```json
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
  "direction": "LONG"
}
```

Az aktuális Phase 2 contract már részletes `marketStructure`, `fvg`,
`execution` és `features` blokkokat is tartalmaz.

## Endpoint

```http
POST /api/v1/webhooks/tradingview
Content-Type: application/json
```

Valid payload esetén az API gyors `202 Accepted` választ ad. Ez azt jelenti,
hogy a payload contract szerint érvényes és feldolgozásra átadható. Az
`eventId` alapján az endpoint idempotensen kezeli az ismételt beküldést; az első
beküldés `ACCEPTED`, az ismételt beküldés `DUPLICATE` státuszt kap.

A válasz `setupScore` blokkja az aktuális determinisztikus scoring configgal
számolt eredményt tartalmazza. Duplikált `eventId` esetén a score az elsőként
eltárolt payloadból számolódik, nem az ismételt beküldés esetleges eltérő
tartalmából.

```json
{
  "status": "ACCEPTED",
  "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
  "eventType": "SETUP_CANDIDATE",
  "schemaVersion": "1.0",
  "receivedAt": "2026-09-03T10:00:00Z",
  "firstReceivedAt": "2026-09-03T10:00:00Z",
  "setupScore": {
    "score": 100.0,
    "accepted": true,
    "strategyVersion": "smc-rce-v1",
    "configVersion": "rule-score-v1",
    "components": [],
    "rejectionReasons": [],
    "positiveReasons": [],
    "negativeReasons": []
  },
  "message": "TradingView webhook payload accepted for processing."
}
```

Ismételt `eventId` esetén:

```json
{
  "status": "DUPLICATE",
  "eventId": "BTCUSDT-1m-1720000000-bullish-choch",
  "eventType": "SETUP_CANDIDATE",
  "schemaVersion": "1.0",
  "receivedAt": "2026-09-03T10:00:30Z",
  "firstReceivedAt": "2026-09-03T10:00:00Z",
  "setupScore": {
    "score": 100.0,
    "accepted": true,
    "strategyVersion": "smc-rce-v1",
    "configVersion": "rule-score-v1",
    "components": [],
    "rejectionReasons": [],
    "positiveReasons": [],
    "negativeReasons": []
  },
  "message": "TradingView webhook payload was already accepted."
}
```

Hibás payload esetén az API `422 Unprocessable Entity` választ ad. A validációs
hibaválasz nem echozza vissza a nyers input értékeket.

## Persistence

A webhook ingestion repository két módban indulhat:

- `WEBHOOK_EVENT_REPOSITORY=memory`: gyors lokális fejlesztés, tartós mentés
  nélkül.
- `WEBHOOK_EVENT_REPOSITORY=postgres`: SQLAlchemy alapú mentés a PostgreSQL
  `webhook_events` táblába.

Docker Compose alatt a backend `postgres` módban indul. A `webhook_events`
tábla `event_id` elsődleges/unique kulccsal védi az idempotenciát.

## Audit

A webhook flow három első audit eseményt ír:

- `WEBHOOK_ACCEPTED`: új, valid webhook esemény.
- `WEBHOOK_DUPLICATE`: már látott `eventId` ismételt beküldése.
- `WEBHOOK_VALIDATION_FAILED`: FastAPI/Pydantic validációs hiba.

Az audit metadata nem tartalmaz nyers webhook payloadot. Hibás payloadnál csak
HTTP metódus, útvonal, hibaszám és validációs hibatípusok kerülnek auditba.

## Teljes példa

```json
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
    "bos": false,
    "choch": true,
    "liquiditySweep": true
  },
  "fvg": {
    "lower": 65120.0,
    "upper": 65240.0,
    "equilibrium": 65180.0,
    "sizeAtrRatio": 0.42,
    "mitigationPercent": 0.0
  },
  "execution": {
    "entry": 65180.0,
    "stopLoss": 64980.0,
    "takeProfit": 65780.0,
    "riskReward": 3.0
  },
  "features": {
    "atr": 285.0,
    "relativeVolume": 1.7,
    "displacementScore": 0.81,
    "session": "NEW_YORK"
  }
}
```

## Validációs szabályok

- `schemaVersion` jelenleg csak `1.0` lehet.
- `eventType` jelenleg `SETUP_CANDIDATE`.
- `source` jelenleg `TRADINGVIEW`.
- `eventId` kötelező, később ez lesz az idempotens deduplikáció kulcsa.
- `timeframe` és `marketStructure.htfTimeframe` pozitív perces érték vagy `D`,
  `W`, `M` lehet.
- `barCloseTime` későbbi kell legyen, mint `barOpenTime`.
- LONG iránynál `stopLoss < entry < takeProfit`.
- SHORT iránynál `takeProfit < entry < stopLoss`.
- `riskReward` legfeljebb 0.01 eltéréssel egyezzen meg az
  `abs(takeProfit - entry) / abs(entry - stopLoss)` képlettel.
- `fvg.lower < fvg.upper`, és az equilibrium a zónán belül van.
- Extra mező nem engedélyezett, hogy a contract explicit maradjon.
- A Pine prototípusból érkező payloadnál az `features.atr` lehet `null`, ha az
  ATR még nem számolható a chart adott pontján.
- Ha a TradingView instrumentumhoz nincs exchange prefix, a Pine prototípus
  `UNKNOWN` exchange értéket küld üres string helyett.

## JSON Schema

A generált schema helye:

- `docs/contracts/generated/tradingview-webhook.schema.json`

Újragenerálás:

```bash
cd apps/api
/Users/bencevarga/Library/Python/3.10/bin/uv run python ../../scripts/export_tradingview_schema.py
```

## Kapcsolódó kód

- `tradingview/indicators/smc_assistant_prototype.pine`
- `apps/api/src/smc_assistant/api/webhooks.py`
- `apps/api/src/smc_assistant/api/errors.py`
- `apps/api/src/smc_assistant/application/audit.py`
- `apps/api/src/smc_assistant/application/webhook_ingestion.py`
- `apps/api/src/smc_assistant/infrastructure/logging_audit.py`
- `apps/api/src/smc_assistant/infrastructure/in_memory_webhook_events.py`
- `apps/api/src/smc_assistant/infrastructure/sql_webhook_events.py`
- `apps/api/src/smc_assistant/infrastructure/webhook_event_schema.py`
- `apps/api/src/smc_assistant/contracts/tradingview.py`
- `apps/api/tests/contracts/test_tradingview_contract.py`
- `apps/api/tests/test_tradingview_webhook_api.py`
- `apps/api/tests/test_webhook_ingestion.py`
- `apps/api/tests/test_sql_webhook_events.py`
