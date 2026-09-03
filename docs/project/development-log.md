# Fejlesztési napló

Ez a napló röviden rögzíti, hol tart a fejlesztés. A részletes végrehajtási
terv továbbra is a `docs/exec-plans/active/full-project.md` fájlban él.

## Forrásbrief

Az eredeti, teljes projektindító utasítás itt van elmentve:

- `docs/project/original-project-brief.md`

Ezt tekintjük a projekt magas szintű termék- és architektúra-briefjének. Ha
ellentmondás lenne a brief és a későbbi implementáció között, akkor döntést
ADR-ben vagy az ExecPlanben kell rögzíteni.

## Aktuális fő munkakönyvtár

- `/Users/bencevarga/Projects/cx2`

A korábbi `Documents/ChatGPT/cx2` munkapéldány már nem aktív, és a Trash alá
lett áthelyezve.

## 2026-08-07 állapot

### Elkészült

- Phase 0 bootstrap elkészült.
- Backend skeleton létrejött FastAPI-val.
- Backend `/health` és `/ready` endpoint működik.
- Frontend skeleton létrejött React, Vite és TypeScript alapon.
- Frontend státuszoldal lekéri és megjeleníti a backend health állapotot.
- Docker Compose konfiguráció létrejött PostgreSQL-lel.
- `.env.example` létrejött valódi secret nélkül.
- GitHub Actions CI workflow létrejött.
- Dokumentációs struktúra létrejött.
- `AGENTS.md`, `ARCHITECTURE.md`, `README.md`, `docs/PLANS.md` elkészült.
- Aktív ExecPlan létrejött.
- Phase 0 learning dokumentum elkészült.
- Első ADR elkészült a moduláris monolit döntésről.
- Phase 1 első kis domain lépése elkészült: risk-reward és R-multiple számítás.

### Ellenőrzött kapuk

- Backend dependency sync: sikeres `uv` + Python 3.12.13 környezetben.
- Backend tests: 5 teszt sikeres.
- Backend lint: sikeres.
- Backend type check: sikeres.
- Frontend tests: 1 teszt sikeres.
- Frontend lint: sikeres.
- Frontend type check: sikeres.
- Frontend audit: 0 sérülékenység.
- Lokális smoke test: backend `/health` és frontend HTML válasz sikeres.

### Nem ellenőrzött vagy részben nyitott

- Docker image build még nem futott végig, mert a Docker daemon nem futott.
- PostgreSQL persistence még nincs implementálva.
- Webhook endpoint még nincs implementálva.
- Pine Script prototípus még nincs implementálva.
- Backtest, journal, ML és AI magyarázati réteg későbbi fázis.

## 2026-09-02 állapot

### Elkészült

- Létrejött az OHLCV `Candle` domain modell.
- Létrejött a confirmed swing high / swing low pivot algoritmus.
- A pivot felismerési ideje explicit: `confirmed_at_index`.
- Unit tesztek készültek az OHLC validációra és a késleltetett pivot
  felismerésre.
- A market structure dokumentáció frissült.
- Létrejött a Phase 1 learning dokumentum első változata.
- Létrejött az első BOS detektor known pivot, close confirmation és break
  buffer támogatással.
- Unit tesztek készültek bullish BOS, bearish BOS, wick-only törés, break
  buffer, ismeretlen pivot és deduplikáció esetekre.
- Létrejött az első CHoCH klasszifikáció `MarketBias` állapottal.
- Unit tesztek készültek bullish CHoCH, bearish CHoCH, azonos irányú BOS,
  semleges induló bias és időrendi rendezés eseteire.
- Létrejött az első háromgyertyás Fair Value Gap domain modell.
- Unit tesztek készültek bullish FVG, bearish FVG, érintkező gyertyák, kevés
  adat, abszolút méretszűrés, tick alapú méretszűrés és átfedő ablakok eseteire.
- Létrejött az első liquidity sweep domain modell.
- Unit tesztek készültek bullish sweep, bearish sweep, későbbi visszazárás,
  megerősítési ablak, még nem ismert pivot, érintés, sweep buffer és
  deduplikáció eseteire.
- Létrejött az első displacement assessment domain modell.
- Unit tesztek készültek iránymeghatározásra, prior ATR-re, erős displacementre,
  hiányzó volumenre, consecutive gyertyákra, kevés ATR adatra és invalid
  beállításokra.
- Létrejött a Phase 1 szintetikus OHLCV példaadatsor.
- Létrejött egy integrált domain teszt, amely ugyanazon mini charton ellenőrzi a
  swing, BOS, CHoCH, FVG, liquidity sweep és displacement eseményeket.

### Ellenőrzött kapuk

- `uv run pytest`: 22 teszt sikeres.
- `uv run ruff check .`: sikeres.
- `uv run mypy src`: sikeres.
- Célzott BOS ellenőrzés: `uv run pytest tests/test_market_structure.py`
  13 teszt sikeres.
- Célzott Ruff ellenőrzés: sikeres.
- Célzott CHoCH ellenőrzés: `uv run pytest tests/test_market_structure.py`
  18 teszt sikeres.
- Teljes backend ellenőrzés CHoCH után: `uv run pytest` 27 teszt sikeres,
  `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott FVG ellenőrzés: `uv run pytest tests/test_fair_value_gaps.py`
  9 teszt sikeres.
- Célzott FVG Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés FVG után: `uv run pytest` 36 teszt sikeres,
  `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott liquidity ellenőrzés: `uv run pytest tests/test_liquidity.py`
  9 teszt sikeres.
- Célzott liquidity Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés liquidity után: `uv run pytest` 45 teszt sikeres,
  `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott displacement ellenőrzés: `uv run pytest tests/test_displacement.py`
  10 teszt sikeres.
- Célzott displacement Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés displacement után: `uv run pytest` 55 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott szintetikus példa ellenőrzés:
  `uv run pytest tests/test_phase1_synthetic_examples.py` 1 teszt sikeres.
- Célzott szintetikus példa Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés szintetikus példák után: `uv run pytest` 56 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Megjegyzés: a FastAPI TestClient egy upstream Starlette deprecation warningot
  jelez, de a tesztek sikeresek.

### Következő konkrét lépés

Phase 1 következő mérföldkő:

1. Phase 2 indítása: TradingView webhook contract Pydantic modelljei.
2. Verziózott payload séma létrehozása.
3. Webhook validációs tesztek.
4. JSON Schema export előkészítése.

## Korábbi következő konkrét lépés

Phase 1 következő mérföldkő:

1. OHLCV gyertya domain modell létrehozása.
2. Megerősített swing high / swing low pivot algoritmus implementálása.
3. Unit tesztek bullish és bearish példákkal.
4. Dokumentáció frissítése a pivot késleltetett felismeréséről.

Fontos szabály: a pivot csak akkor tekinthető ismertnek, amikor a szükséges
jobb oldali gyertyák már lezárultak. Ez védi a rendszert a future leakage és a
repainting félreértésektől.

## 2026-09-02 Phase 2 állapot

### Elkészült

- Létrejött a TradingView webhook első Pydantic contract modellje.
- A contract validálja a verziót, eseménytípust, forrást, timeframe-et,
  időbélyegeket, market structure, FVG, execution és feature blokkokat.
- A `riskReward` mezőt összeveti az entry/stop/target képlettel.
- Extra payload mezők tiltottak.
- Létrejött a JSON Schema export script.
- Létrejött a generált JSON Schema fájl.
- Létrejött a Phase 2 learning dokumentum első változata.
- Létrejött a `POST /api/v1/webhooks/tradingview` endpoint.
- Valid payloadra az API gyors `202 Accepted` választ ad.
- Hibás payloadnál az API validációs válasza nem echozza vissza a nyers input
  értékeket.
- Létrejött az első idempotens webhook ingestion application service.
- Létrejött az in-memory webhook event repository tesztduplum.
- Az API ismételt `eventId` esetén `DUPLICATE` státusszal tér vissza, és az első
  beküldés `firstReceivedAt` idejét mutatja.
- Létrejött az első SQLAlchemy alapú webhook event repository.
- Létrejött a `webhook_events` adatbázistábla séma `event_id` unique kulccsal.
- A `WEBHOOK_EVENT_REPOSITORY` kapcsolóval választható a `memory` és a `postgres`
  repository.
- Docker Compose alatt a backend már `postgres` repository módban indul.
- Létrejött az első típusos audit event modell.
- A webhook ingestion `WEBHOOK_ACCEPTED` és `WEBHOOK_DUPLICATE` audit eseményeket
  ír.
- A validációs hiba handler `WEBHOOK_VALIDATION_FAILED` audit eseményt ír,
  nyers payload nélkül.

### Ellenőrzött kapuk

- Célzott contract ellenőrzés:
  `uv run pytest tests/contracts/test_tradingview_contract.py` 12 teszt sikeres.
- Célzott contract Ruff és mypy ellenőrzés: sikeres.
- JSON Schema export: sikeres.
- Teljes backend ellenőrzés webhook contract után: `uv run pytest` 68 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott webhook API ellenőrzés:
  `uv run pytest tests/test_tradingview_webhook_api.py` 3 teszt sikeres.
- Teljes backend ellenőrzés webhook endpoint után: `uv run pytest` 71 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott webhook ingestion ellenőrzés:
  `uv run pytest tests/test_webhook_ingestion.py tests/test_tradingview_webhook_api.py`
  7 teszt sikeres.
- Teljes backend ellenőrzés idempotens ingestion után: `uv run pytest` 75 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Célzott SQL webhook repository ellenőrzés:
  `uv run pytest tests/test_sql_webhook_events.py tests/test_webhook_ingestion_factory.py`
  4 teszt sikeres.
- Teljes backend ellenőrzés SQL persistence után: `uv run pytest` 79 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Docker Compose konfiguráció ellenőrzés: `docker compose config` sikeres.
- Célzott audit ellenőrzés:
  `uv run pytest tests/test_webhook_ingestion.py tests/test_tradingview_webhook_api.py tests/test_webhook_ingestion_factory.py`
  8 teszt sikeres.
- Teljes backend ellenőrzés audit után: `uv run pytest` 79 teszt sikeres,
  `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Docker daemon ellenőrzés: nem sikeres, mert a Docker daemon nem futott.

### Következő konkrét lépés

Phase 2 következő mérföldkő:

1. Phase 2 lezáró Docker/PostgreSQL smoke teszt, ha a Docker daemon fut.
2. Alembic migrációs stratégia bevezetése a `create_all` helyett.
3. Phase 3 indítása: Pine Script prototípus.
4. Swing/BOS/CHoCH/FVG/liquidity/displacement jelölések TradingView oldalon.
5. JSON alert payload összehangolása a backend contracttal.

## 2026-09-03 Phase 3 állapot

### Elkészült

- Létrejött az első TradingView Pine Script indikátor prototípus:
  `tradingview/indicators/smc_assistant_prototype.pine`.
- A prototípus swing high / swing low, BOS/CHoCH, FVG, liquidity sweep és
  displacement jelölési alapokat tartalmaz.
- Létrejött a backend webhook contract kulcsmezőihez igazított JSON alert
  payload váz.
- A payload `execution` blokkja első körben FVG equilibrium entryt, FVG-n kívüli
  stopot, fix 2R targetet és ebből számolt risk-reward értéket használ.
- Létrejött a Phase 3 learning dokumentum első változata.

### Ellenőrzött kapuk

- Célzott Pine prototípus statikus ellenőrzés:
  `uv run pytest tests/test_tradingview_pine_prototype.py` 4 teszt sikeres.
- Teljes backend ellenőrzés Pine prototípus után: `uv run pytest` 83 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- TradingView editor visszajelzés alapján a több soros Pine függvényhívások
  egy soros formára lettek alakítva, mert `Mismatched input 'end of line without
  line continuation' expecting ')'` hibát okozhatnak.
- TradingView képernyőkép alapján az első vizuális nézet túl zajos volt. Az
  indikátor clean alapbeállításra váltott: 5/5 pivot ablak, swing/BOS/sweep/
  displacement debug elemek alapból kikapcsolva, FVG-ből alapból csak setuphoz
  kapcsolódó zóna.
- Újabb TradingView képernyőkép alapján a clean nézet túl üres lett. Az
  indikátor balanced alapbeállításra váltott: 3/3 pivot ablak, BOS/CHoCH label
  alapból bekapcsolva, sweep/displacement/swing debug elemek kikapcsolva, FVG
  boxokból egyszerre legfeljebb 8 látszik.
- A balanced nézethez bekerült a legutóbbi swing high / swing low szint
  jobbra nyúló vonalakkal, valamint egy aktuális bias badge. Így akkor is van
  strukturális kontextus, amikor nincs friss BOS/CHoCH esemény a képernyőn.
- Frissített Pine statikus ellenőrzés:
  `uv run pytest tests/test_tradingview_pine_prototype.py` 8 teszt sikeres.
- Teljes backend ellenőrzés struktúraszintek után: `uv run pytest` 87 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- A BOS/CHoCH logika finomítva lett: a break ellenőrzés a bar elején ismert,
  figyelt swing szinteken fut, és csak utána frissül az újonnan megerősített
  pivot. Ez csökkenti annak kockázatát, hogy egy friss pivot-visszaigazolás
  eltakarjon egy tényleges structure breaket.
- A bias badge semleges állapotból már megerősített swing-sorozat alapján is
  irányt tud találni: HH/HL esetén bullish, LH/LL esetén bearish kontextus.
- Frissített Pine statikus ellenőrzés bias finomítás után:
  `uv run pytest tests/test_tradingview_pine_prototype.py` 10 teszt sikeres.
- Teljes backend ellenőrzés bias finomítás után: `uv run pytest` 89 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- A Pine alert payload össze lett hangolva a backend contracttal az opcionális
  értékek szintjén is: hiányzó prior ATR esetén `null`, üres TradingView
  exchange prefix esetén `UNKNOWN` kerül a JSON-ba.
- A backend contract kapott reprezentatív Pine-szerű LONG és SHORT payload
  teszteket, 2R executionnel, `relativeVolume: null` értékkel és nullable ATR
  esettel.
- Célzott Pine/contract összevetés:
  `uv run pytest tests/contracts/test_tradingview_contract.py tests/test_tradingview_pine_prototype.py`
  25 teszt sikeres.
- Teljes backend ellenőrzés Pine/contract összevetés után: `uv run pytest`
  92 teszt sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.

### Nem ellenőrzött vagy részben nyitott

- Pine fordítás lokálisan nem ellenőrizhető TradingView editor nélkül.
- Az `execution` blokk még prototípus logika, nem végleges kereskedési szabály.

### Következő konkrét lépés

1. Pine script újratesztelése TradingView editorban a balanced alapnézettel és
   a bias bootstrap viselkedésével.
2. Tényleges TradingView alert kézi beküldése a lokális webhook endpoint felé.
3. Repainting kockázatok dokumentálása TradingView szemszögből.

## 2026-09-03 Phase 4 állapot

### Elkészült

- Elindult a rule-based setup scoring fázis.
- Létrejött az első determinisztikus domain scoring modul:
  `apps/api/src/smc_assistant/domain/setup_scoring.py`.
- A scoring 0-100 közötti pontszámot ad HTF bias, CHoCH, liquidity sweep,
  displacement, FVG size/ATR, session és risk-reward komponensekből.
- Az eredmény tartalmaz strategy versiont, scoring config versiont,
  komponenspontokat, pozitív okokat, negatív okokat és hard reject okokat.
- Az első hard reject okok: ellenirányú HTF bias, hiányzó CHoCH, minimum alatti
  risk-reward és acceptance threshold alatti score.
- Létrejött a Phase 4 learning dokumentum első változata.

### Ellenőrzött kapuk

- Célzott scoring ellenőrzés: `uv run pytest tests/test_setup_scoring.py`
  8 teszt sikeres.
- Célzott scoring Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés scoring alap után: `uv run pytest` 100 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Létrejött a TradingView webhook payload -> `SetupScoringInput` application
  mapper.
- A webhook ingestion flow már score-t számol a valid setup candidate payloadra.
- Az API válasz `setupScore` blokkot ad vissza komponenspontokkal,
  config verzióval, pozitív/negatív indokokkal és reject okokkal.
- Duplikált `eventId` esetén a score az elsőként eltárolt payloadból számolódik,
  nem az ismételt beküldés tartalmából.
- Az audit metadata tartalmazza a score-t, az accepted flaget és a scoring config
  verziót, de továbbra sem tartalmaz nyers payloadot.
- Célzott scoring/ingestion/API ellenőrzés:
  `uv run pytest tests/test_setup_scoring_mapping.py tests/test_webhook_ingestion.py tests/test_tradingview_webhook_api.py`
  9 teszt sikeres.
- Célzott scoring ingestion Ruff és mypy ellenőrzés: sikeres.
- Teljes backend ellenőrzés scoring ingestion után: `uv run pytest` 102 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
- Létrejött a pontozott `SetupCandidateRecord` belső séma.
- Létrejött az idempotens in-memory setup candidate repository.
- Létrejött az SQLAlchemy alapú `setup_candidates` tábla és repository.
- A `setup_candidates.event_id` unique kapcsolatként mutat a
  `webhook_events.event_id` mezőre.
- Az ingestion flow új webhook eseménynél setup candidate rekordot is ment,
  memory és postgres repository módban is.
- Az API válasz `setupCandidateId` mezővel is visszatér.
- Célzott setup candidate persistence ellenőrzés:
  `uv run pytest tests/test_setup_candidates.py tests/test_sql_setup_candidates.py tests/test_webhook_ingestion.py tests/test_tradingview_webhook_api.py`
  12 teszt sikeres.
- Teljes backend ellenőrzés setup candidate persistence után: `uv run pytest`
  107 teszt sikeres, `uv run ruff check .` sikeres,
  `uv run mypy src` sikeres.

### Következő konkrét lépés

1. Setup lekérdező API első verziójának megtervezése.
2. Setup lista endpoint memory és SQL repository támogatással.
3. Frontend dashboard első setup listájának előkészítése.
