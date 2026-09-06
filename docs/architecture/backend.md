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
