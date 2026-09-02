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

## JSON Schema

A generált schema helye:

- `docs/contracts/generated/tradingview-webhook.schema.json`

Újragenerálás:

```bash
cd apps/api
/Users/bencevarga/Library/Python/3.10/bin/uv run python ../../scripts/export_tradingview_schema.py
```

## Kapcsolódó kód

- `apps/api/src/smc_assistant/contracts/tradingview.py`
- `apps/api/tests/contracts/test_tradingview_contract.py`
