# Phase 04: Rule-based setup scoring

## 1. Mit építettünk?

Elkészült az első determinisztikus setup scoring domain modul:
`apps/api/src/smc_assistant/domain/setup_scoring.py`.

Elkészült a TradingView payload -> scoring input application mapper is:
`apps/api/src/smc_assistant/application/setup_scoring.py`.

Elkészült a pontozott setup candidate belső rekordja és első repository rétege:

- `apps/api/src/smc_assistant/application/setup_candidates.py`
- `apps/api/src/smc_assistant/infrastructure/in_memory_setup_candidates.py`
- `apps/api/src/smc_assistant/infrastructure/sql_setup_candidates.py`

A cél az, hogy egy setup candidate reprodukálható, auditálható 0-100 közötti
pontszámot kapjon, és ez a pontozási snapshot később listázható, backtestelhető
és journalhoz kapcsolható legyen.

Az első komponensek:

- HTF bias egyezése;
- CHoCH megléte;
- liquidity sweep megléte;
- displacement score;
- FVG size/ATR ratio;
- session;
- risk-reward.

## 2. Miért erre van szükség?

A Pine és a webhook réteg már setup candidate eseményeket tud előállítani és
fogadni. A következő értékteremtő lépés annak eldöntése, hogy ezek közül melyik
érdemes figyelemre, elutasításra vagy későbbi backtest/journal elemzésre.

A scoring determinisztikus, tehát ugyanarra az inputra és config verzióra mindig
ugyanazt az eredményt adja. Ez később fontos lesz a backtest, az ML dataset és
az AI magyarázati réteg auditálhatóságához.

## 3. Fontos döntések

- Az alapértelmezett score súlyai összesen pontosan 100-at adnak.
- A `rule-score-v1` config verzió explicit része az eredménynek.
- A semleges HTF bias fél pontot kap, nem hard reject.
- Az ellenirányú HTF bias hard reject.
- A hiányzó CHoCH hard reject.
- A minimum alatti risk-reward hard reject.
- A liquidity sweep hiánya egyelőre negatív komponens, de nem hard reject.
- A webhook ingestion flow az elsőként eltárolt payloadból számolja a score-t.
  Duplikált `eventId` esetén ezért nem az ismételt beküldés tartalma írja felül
  a pontozási eredményt.
- Az API válaszban a `setupScore` blokk már láthatóvá teszi az összpontszámot,
  az elfogadási döntést, a komponenseket és az indokokat.
- A `setup_candidates` tábla külön tárolja a pontozott setup candidate rekordot,
  `event_id` unique kapcsolattal a `webhook_events` táblára.
- A `setup_id` jelenleg determinisztikusan megegyezik az `event_id` értékkel.
  Ezt később lehet külön UUID-re cserélni, ha több setup is származhat egyetlen
  külső eseményből.
- A memory és SQL repository is idempotens `event_id` alapján.

## 4. Kapcsolódó fájlok

- `apps/api/src/smc_assistant/domain/setup_scoring.py`
- `apps/api/src/smc_assistant/application/setup_scoring.py`
- `apps/api/src/smc_assistant/application/setup_candidates.py`
- `apps/api/src/smc_assistant/infrastructure/in_memory_setup_candidates.py`
- `apps/api/src/smc_assistant/infrastructure/sql_setup_candidates.py`
- `apps/api/tests/test_setup_scoring.py`
- `apps/api/tests/test_setup_scoring_mapping.py`
- `apps/api/tests/test_setup_candidates.py`
- `apps/api/tests/test_sql_setup_candidates.py`
- `docs/strategy/setup-scoring.md`
- `tradingview/indicators/smc_assistant_prototype.pine`
- `apps/api/src/smc_assistant/contracts/tradingview.py`

## 5. Következő lépés

A következő Phase 4 szeletben az első setup lekérdező API-t kell előkészíteni.
Ezzel a beérkezett és pontozott setupok már nemcsak webhook válaszként, hanem
külön endpointon is megjelenhetnek.
