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
