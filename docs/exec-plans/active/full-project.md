# ExecPlan: teljes projekt

## Cél

Fokozatosan felépíteni egy működő, tesztelt és dokumentált SMC/ICT-inspired
trading setup elemző és AI-támogatott kereskedési asszisztenst.

## Hatókör

Az MVP moduláris monolitként indul:

- FastAPI backend;
- React/Vite frontend;
- PostgreSQL adatbázis;
- TradingView webhook contract;
- determinisztikus setup scoring;
- journal, backtest, paper trading;
- később auditálható ML és LLM magyarázati réteg.

## Phase 0: Discovery és bootstrap

- [x] Repository felmérése.
- [x] Rövid projektösszefoglaló rögzítése.
- [x] `AGENTS.md` létrehozása.
- [x] Dokumentációs könyvtárstruktúra létrehozása.
- [x] `docs/PLANS.md` létrehozása.
- [x] Aktív teljes projekt ExecPlan létrehozása.
- [x] Phase 0 részletes mérföldkövek rögzítése.
- [x] Backend skeleton létrehozása.
- [x] Frontend skeleton létrehozása.
- [x] PostgreSQL Docker Compose konfiguráció.
- [x] `.env.example` secret nélkül.
- [x] Backend `/health` és `/ready` endpoint.
- [x] Minimális frontend státuszoldal.
- [x] Lint, type check és teszt konfiguráció.
- [x] GitHub Actions workflow.
- [x] Releváns ellenőrzések futtatása.
- [x] `docs/learning/phase-00-bootstrap.md` létrehozása.

### Phase 0 ellenőrzések

Tervezett parancsok:

```bash
cd apps/api && uv sync --all-extras --dev
cd apps/api && uv run pytest
cd apps/api && uv run ruff check .
cd apps/api && uv run mypy src
cd apps/web && npm install
cd apps/web && npm run test
cd apps/web && npm run lint
cd apps/web && npm run typecheck
```

Tényleges eredmény:

- `uv sync --all-extras --dev`: sikeres, Python 3.12.13 környezetben.
- `uv run pytest`: sikeres, 5 teszt átment.
- `uv run ruff check .`: sikeres.
- `uv run mypy src`: sikeres.
- `npm install`: sikeres, lockfile létrejött.
- `npm run test`: sikeres, 1 teszt átment.
- `npm run lint`: sikeres.
- `npm run typecheck`: sikeres.
- `npm audit`: sikeres, 0 sérülékenység.

Környezeti megjegyzés: a Docker CLI telepítve van, de a daemon nem futott,
ezért a Docker image build ebben a munkamenetben nem volt futtatható.

## Phase 1: Domain modell

- [x] Első domain mérföldkő: alap trading enumok és risk-reward számítás.
- [x] Risk-reward unit tesztek.
- [x] Trading glossary első változata.
- [x] Strategy specification első változata.
- [x] Swing high/low algoritmikus definíció és unit tesztek.
- [x] BOS algoritmikus definíció és unit tesztek.
- [x] CHoCH algoritmikus definíció és unit tesztek.
- [x] FVG algoritmikus definíció és unit tesztek.
- [x] Liquidity sweep algoritmikus definíció és unit tesztek.
- [x] Displacement komponensek és unit tesztek.
- [x] Szintetikus OHLCV példák.

## Phase 2: Webhook ingestion

- [x] Verziózott TradingView webhook contract.
- [x] Pydantic validáció.
- [x] JSON Schema export.
- [x] TradingView webhook HTTP endpoint.
- [x] Első idempotens event feldolgozás `eventId` alapján.
- [x] In-memory webhook event repository tesztduplum.
- [ ] PostgreSQL persistence.
- [ ] Audit események.
- [x] Hibás payloadok biztonságos API válasza nyers input echo nélkül.
- [ ] Hibás payloadok biztonságos naplózása.

## Phase 3: Pine Script prototípus

- [ ] Swing jelölés.
- [ ] BOS/CHoCH jelölés.
- [ ] FVG zónák.
- [ ] Liquidity sweep.
- [ ] Displacement score.
- [ ] JSON alert payload.
- [ ] Repainting kockázatok dokumentálása.

## Phase 4: Rule-based setup scoring

- [ ] Pontozási komponensek.
- [ ] 0-100 közötti score.
- [ ] Elutasítási okok.
- [ ] Strategy configuration versioning.
- [ ] Determinisztikus magyarázat.

## Phase 5: Outcome és backtest

- [ ] OHLCV CSV import.
- [ ] MarketDataProvider interfész.
- [ ] Triple-barrier outcome engine.
- [ ] Commission és slippage.
- [ ] MFE/MAE számítás.
- [ ] Backtest analytics.

## Phase 6: Frontend és journal

- [ ] Dashboard.
- [ ] Setup lista.
- [ ] Setup részletező.
- [ ] Journal.
- [ ] Analytics.
- [ ] Frontend tesztek.

## Phase 7: Paper trading workflow

- [ ] Élő TradingView webhook flow.
- [ ] Outcome frissítés.
- [ ] Értesítési adapter.
- [ ] Napi és heti összesítő.

## Phase 8: ML dataset és baseline

- [ ] Feature schema.
- [ ] Dataset builder.
- [ ] Leakage audit.
- [ ] Időalapú split.
- [ ] Dummy baseline.
- [ ] Logisztikus regresszió.

## Phase 9: ML setup filter

- [ ] Rule score kontra ML összehasonlítás.
- [ ] Kalibrált valószínűség.
- [ ] Walk-forward evaluation.
- [ ] Shadow mode inference.

## Phase 10: AI explanation

- [ ] ExplanationProvider interfész.
- [ ] Template fallback.
- [ ] Opcionális OpenAI adapter.
- [ ] Setup és journal magyarázat.

## Phase 11: Hardening

- [ ] Security review.
- [ ] Observability.
- [ ] Backup és restore dokumentáció.
- [ ] E2E teszt.
- [ ] Deployment dokumentáció.

## Állapotnapló

- 2026-08-06: Üres repositoryból Phase 0 bootstrap elindítva. Backend és
  frontend skeleton elkészült, dokumentációs struktúra létrejött. Phase 1 első
  mérföldköveként bekerült a risk-reward domain számítás és teszt.
- 2026-08-07: Az eredeti projektindító brief elmentve a
  `docs/project/original-project-brief.md` fájlba. Létrejött a rövid
  fejlesztési napló: `docs/project/development-log.md`. A fő munkakönyvtár
  innentől `/Users/bencevarga/Projects/cx2`.
- 2026-09-02: Phase 1-ben elkészült az OHLCV `Candle` domain modell és a
  confirmed swing high / swing low pivot algoritmus. A felismerési késleltetés
  `confirmed_at_index` mezőben auditálható. Ellenőrzés: `uv run pytest`
  14 teszt sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres.
  Következő lépés: BOS.
- 2026-09-02: Elkészült az első BOS detektor confirmed pivotokra építve.
  Támogatja a záróáras megerősítést, a `break_buffer` szűrést, a még nem ismert
  pivotok kizárását és az egy pivotra jutó egyszeri eseményt. Célzott
  ellenőrzés: `uv run pytest tests/test_market_structure.py` 13 teszt sikeres,
  célzott Ruff sikeres. Teljes backend ellenőrzés: `uv run pytest` 22 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres. Következő
  lépés: CHoCH.
- 2026-09-02: Elkészült az első CHoCH klasszifikáció `MarketBias` alapján.
  A rendszer időrendbe rendezi a BOS eseményeket, semleges biasból először csak
  kontextust épít, majd az ellentétes irányú structure breakből CHoCH eseményt
  hoz létre. Célzott ellenőrzés: `uv run pytest tests/test_market_structure.py`
  18 teszt sikeres. Teljes backend ellenőrzés: `uv run pytest` 27 teszt
  sikeres, `uv run ruff check .` sikeres, `uv run mypy src` sikeres. Következő
  lépés: FVG.
- 2026-09-02: Elkészült az első háromgyertyás FVG domain modell. Bullish és
  bearish FVG-t detektál, `detected_at_index` mezővel rögzíti a felismerés
  időpontját, és támogat abszolút, valamint tick alapú minimális méretszűrést.
  Célzott ellenőrzés: `uv run pytest tests/test_fair_value_gaps.py` 9 teszt
  sikeres, célzott Ruff és mypy sikeres. Teljes backend ellenőrzés:
  `uv run pytest` 36 teszt sikeres, `uv run ruff check .` sikeres,
  `uv run mypy src` sikeres. Következő lépés: liquidity sweep.
- 2026-09-02: Elkészült az első liquidity sweep domain modell confirmed
  pivotokra építve. Bullish sweep swing low alá szúrást és fölé visszazárást,
  bearish sweep swing high fölé szúrást és alá visszazárást jelent. Támogatott
  a `sweep_buffer`, a `max_confirmation_bars` és az egy pivotra jutó egyszeri
  sweep esemény. Célzott ellenőrzés: `uv run pytest tests/test_liquidity.py`
  9 teszt sikeres, célzott Ruff és mypy sikeres. Teljes backend ellenőrzés:
  `uv run pytest` 45 teszt sikeres, `uv run ruff check .` sikeres,
  `uv run mypy src` sikeres. Következő lépés: displacement.
- 2026-09-02: Elkészült az első displacement assessment domain modell. A score
  prior ATR, body/ATR, range/ATR, body-to-range, consecutive candle és opcionális
  volumen komponensekből áll. Hiányzó ATR vagy volumen esetén a megfelelő
  komponens kimarad és a score a rendelkezésre álló súlyokra normalizálódik.
  Célzott ellenőrzés: `uv run pytest tests/test_displacement.py` 10 teszt
  sikeres, célzott Ruff és mypy sikeres. Teljes backend ellenőrzés:
  `uv run pytest` 55 teszt sikeres, `uv run ruff check .` sikeres,
  `uv run mypy src` sikeres. Következő lépés: szintetikus OHLCV példák.
- 2026-09-02: Elkészült a Phase 1 szintetikus OHLCV példaadatsor és az
  integrált domain teszt. Ugyanazon nyolcgyertyás mini charton ellenőrzi a
  swing, BOS, CHoCH, FVG, liquidity sweep és displacement eseményeket. Célzott
  ellenőrzés: `uv run pytest tests/test_phase1_synthetic_examples.py` 1 teszt
  sikeres, célzott Ruff és mypy sikeres. Teljes backend ellenőrzés:
  `uv run pytest` 56 teszt sikeres, `uv run ruff check .` sikeres,
  `uv run mypy src` sikeres. Phase 1 domain alapok lezárva. Következő lépés:
  Phase 2 webhook ingestion contract.
- 2026-09-02: Phase 2-ben elkészült a TradingView webhook első verziózott
  Pydantic contractja és a generált JSON Schema. A contract tiltja az extra
  mezőket, validálja a timeframe-et, bar időrendet, FVG határokat, execution
  sorrendet és a `riskReward` képletet. Célzott ellenőrzés:
  `uv run pytest tests/contracts/test_tradingview_contract.py` 12 teszt
  sikeres, célzott Ruff és mypy sikeres, JSON Schema export sikeres. Teljes
  backend ellenőrzés: `uv run pytest` 68 teszt sikeres, `uv run ruff check .`
  sikeres, `uv run mypy src` sikeres. Következő lépés: webhook endpoint.
- 2026-09-03: Elkészült a `POST /api/v1/webhooks/tradingview` endpoint. Valid
  payloadra gyors `202 Accepted` választ ad, a tényleges idempotens feldolgozás
  és persistence előtt. A FastAPI validációs hibaválasz nyers input echo nélkül
  tér vissza, így hibás webhooknál sem kerül vissza például véletlenül beküldött
  secret érték a kliensnek. Következő lépés: idempotens event feldolgozás.
- 2026-09-03: Elkészült az első idempotens webhook ingestion service. Az
  `eventId` az idempotencia kulcsa: az első beküldés `ACCEPTED`, az ismételt
  beküldés `DUPLICATE` státuszt kap, és a rendszer az elsőként eltárolt payloadot
  tartja meg. Az első repository in-memory, lockkal védett tesztduplum; a
  következő lépés ennek PostgreSQL persistence-re cserélése.
