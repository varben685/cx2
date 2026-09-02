# Phase 02: Webhook contract

## 1. Mit építettünk?

Elkészült a TradingView webhook első verziózott Pydantic contractja. A modell
validálja a `schemaVersion`, `eventId`, `eventType`, `source`, timeframe,
bar-időbélyeg, market structure, FVG, execution és feature mezőket.

## 2. Miért erre van szükség?

A TradingView alert egy külső rendszerből érkezik. A backend csak akkor tud
auditálhatóan és biztonságosan dolgozni vele, ha a payload formája explicit,
tesztelt és verziózott.

## 3. Hogyan működik a háttérben?

A contract camelCase JSON mezőket fogad, például `schemaVersion`,
`barOpenTime`, `marketStructure`. Pythonban ezek snake_case attribútumokká
válnak, például `schema_version`, `bar_open_time`, `market_structure`.

```mermaid
flowchart LR
    TV[TradingView JSON] --> P[Pydantic validation]
    P --> OK[Validated payload]
    P --> ERR[Validation error]
    OK --> S[JSON Schema export]
```

## 4. Milyen alternatívák léteznek?

- Laza `dict` alapú payload kezelés.
- JSON Schema kézi írása Pydantic modell nélkül.
- Külön OpenAPI-first contract generálás.

## 5. Miért ezt választottuk?

A Pydantic modell közvetlenül illeszkedik a FastAPI-hoz, runtime validációt ad,
és JSON Schema is generálható belőle. Így egyetlen forrásból kapunk validációt
és dokumentálható contractot.

## 6. Milyen trading fogalmak kapcsolódnak hozzá?

- Setup candidate: még nem trade, hanem elemzésre beküldött setup jelölt.
- HTF bias: magasabb idősíkú irányultság.
- FVG: a setuphoz tartozó Fair Value Gap zóna.
- Risk-reward: az entry, stop loss és take profit távolságából számolt arány.

## 7. Milyen hibák vagy félreértések fordulhatnak elő?

- A webhook payload nem tartalmazhat API-kulcsot vagy jelszót.
- A `riskReward` mező nem önálló igazság: egyeznie kell az entry/stop/target
  képlettel.
- A `eventId` még nem adatbázisos deduplikáció, de már kötelező contract mező.
- Extra mezőket most tiltunk, hogy ne csússzon be dokumentálatlan adat.

## 8. Mely fájlokat érdemes elolvasni?

- `apps/api/src/smc_assistant/contracts/tradingview.py`
- `apps/api/tests/contracts/test_tradingview_contract.py`
- `docs/contracts/tradingview-webhook.md`
- `docs/contracts/generated/tradingview-webhook.schema.json`
- `scripts/export_tradingview_schema.py`

## 9. Hogyan lehet manuálisan kipróbálni?

```bash
cd apps/api
/Users/bencevarga/Library/Python/3.10/bin/uv run pytest tests/contracts/test_tradingview_contract.py
/Users/bencevarga/Library/Python/3.10/bin/uv run python ../../scripts/export_tradingview_schema.py
```

## 10. Gyakorlófeladat

Változtasd meg a teszt payloadban a `riskReward` értéket 3.0-ról 2.0-ra, és
figyeld meg, hogy a validáció elutasítja a payloadot.

