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

## Következő konkrét lépés

Phase 1 következő mérföldkő:

1. OHLCV gyertya domain modell létrehozása.
2. Megerősített swing high / swing low pivot algoritmus implementálása.
3. Unit tesztek bullish és bearish példákkal.
4. Dokumentáció frissítése a pivot késleltetett felismeréséről.

Fontos szabály: a pivot csak akkor tekinthető ismertnek, amikor a szükséges
jobb oldali gyertyák már lezárultak. Ez védi a rendszert a future leakage és a
repainting félreértésektől.

