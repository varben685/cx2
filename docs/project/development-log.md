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
- Megjegyzés: a FastAPI TestClient egy upstream Starlette deprecation warningot
  jelez, de a tesztek sikeresek.

### Következő konkrét lépés

Phase 1 következő mérföldkő:

1. Liquidity sweep algoritmikus definíció létrehozása confirmed pivotokra
   építve.
2. Bullish és bearish sweep unit tesztek.
3. Visszazárási szabály és opcionális megerősítési ablak előkészítése.
4. Dokumentáció frissítése sweep edge case-ekkel.

## Korábbi következő konkrét lépés

Phase 1 következő mérföldkő:

1. OHLCV gyertya domain modell létrehozása.
2. Megerősített swing high / swing low pivot algoritmus implementálása.
3. Unit tesztek bullish és bearish példákkal.
4. Dokumentáció frissítése a pivot késleltetett felismeréséről.

Fontos szabály: a pivot csak akkor tekinthető ismertnek, amikor a szükséges
jobb oldali gyertyák már lezárultak. Ez védi a rendszert a future leakage és a
repainting félreértésektől.
