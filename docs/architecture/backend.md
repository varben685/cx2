# Backend

A backend FastAPI alkalmazás. Az induló szerkezet:

- `api`: HTTP route-ok.
- `application`: use case-ek.
- `domain`: tiszta üzleti logika.
- `infrastructure`: adatbázis és adapterek.
- `analytics`: mutatók.
- `ml`: baseline modellek.

Az első működő végpontok:

- `GET /health`
- `GET /ready`

## Backtest analytics

A `GET /api/v1/analytics/summary` kötelező `runId` és opcionális `symbol`
paraméterből olvassa a tárolt futás teljes eredménysorát. Az application
réteg a repositorytól kér adatot, az `analytics/backtest.py` pedig tiszta
Python összesítést végez. A camelCase HTTP contractot Pydantic modell adja.

Az outcome repository a meglévő service factoryban jön létre: `memory`
módban in-memory adapter, `postgres` módban a webhook/setup adapterekkel
közös engine-t használó SQL repository. A módot a meglévő
`WEBHOOK_EVENT_REPOSITORY` beállítás választja ki.

Az endpoint olvasásra szolgál. Nem indít backtestet és nem hoz létre
eredményrekordot. Részletek: `docs/contracts/backtest-analytics.md`.

## Backtest workflow

Az új `POST /api/v1/backtests` végpont a JSON-ban kapott CSV-t és validált
TradingView setupokat adja a batch application folyamatnak. A
`evaluate_tradingview_record` mentés nélkül épít végleges outcome-ot, majd
a backtest repository egyszerre menti a run és outcome sorokat.

A service factory memory vagy PostgreSQL adaptert hoz létre a backtesthez
is, az outcome repositoryval közös tárolón. A run lista/részletező és az
outcome lista/részletező külön HTTP nézet, mindkettő camelCase modellekkel.
API contract: `docs/contracts/backtests.md`. Tárolási döntés: ADR-0003.
