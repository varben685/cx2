# Setup event schema

Ez a dokumentum a belső setup események sémájának helye. Phase 2-ben a
TradingView webhook contractból Pydantic modellek készülnek, majd ezek alapján
exportálható JSON Schema jön létre.

Alapelv: a belső eseményeknek auditálhatónak, verziózottnak és
újrapontozhatónak kell lenniük.

## Aktuális állapot

Az első külső contract elkészült:

- `apps/api/src/smc_assistant/contracts/tradingview.py`

A webhook payload már alkalmazásszintű scoring inputra mappelhető:

- `apps/api/src/smc_assistant/application/setup_scoring.py`
- `apps/api/src/smc_assistant/domain/setup_scoring.py`
- `apps/api/src/smc_assistant/application/setup_candidates.py`

A webhook ingestion flow az aktuális `rule-score-v1` configgal pontozza a
valid TradingView setup candidate eseményt. Az API válaszban a `setupScore`
blokk tartalmazza az összpontszámot, komponenseket, pozitív/negatív indokokat
és reject okokat.

A tartós, külön `SetupCandidate` adatbázis-entitás első változata elkészült:

- tábla: `setup_candidates`
- repository: `SQLSetupCandidateRepository`
- tesztduplum: `InMemorySetupCandidateRepository`

Jelenleg a `setup_id` megegyezik az idempotens `event_id` értékkel. A score
snapshotként tárolódik: komponenspontok, reject okok, pozitív és negatív indokok
együtt kerülnek a setup candidate rekordba.

## Lekérdező API

Az első setup API endpointok:

```http
GET /api/v1/setups?limit=50&symbol=BTCUSDT&accepted=true
GET /api/v1/setups/{setup_id}
```

A lista endpoint a legfrissebb `received_at` szerint csökkenő sorrendben adja
vissza a setupokat. A `limit` 1 és 100 közötti érték lehet. A `symbol` és
`accepted` query paraméter opcionális szűrő.

Ismeretlen `setup_id` esetén az API `404 Not Found` választ ad.
