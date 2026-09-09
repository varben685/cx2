# Lokális fejlesztés

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Docker Compose alatt az API `WEBHOOK_EVENT_REPOSITORY=postgres` módban indul,
így a valid TradingView webhook események a PostgreSQL `webhook_events`
táblába, a paper trade-ek pedig a `paper_trades` és `paper_trade_events`
táblákba kerülnek. A gyökér `.dockerignore` kihagyja a lokális dependencyket és
cache-eket a build contextből.

## Paper risk beállítások

A `.env.example` tartalmazza az összes `PAPER_*` változót. Docker Compose ezeket
átadja az API-nak. A fontos alapértékek: maximum 1% kockázat trade-enként,
3R napi veszteség, három egymást követő veszteség, minimum 2R terv, legfeljebb
három aktív pozíció, 15 perc cooldown és 70-es minimum setup score.

A `PAPER_CORRELATION_GROUPS` JSON tömbök tömbje, például:

```bash
PAPER_CORRELATION_GROUPS='[["BTCUSDT","ETHUSDT"],["EURUSD","GBPUSD"]]'
```

Az alapérték üres, ezért korrelációs tiltás csak explicit konfiguráció után él.

Az automatikus paper workflow alapértékei:

```bash
PAPER_AUTO_TRADE_ENABLED=true
PAPER_ACCOUNT_BALANCE=10000
PAPER_DEFAULT_RISK_PERCENT=1
```

A `PAPER_AUTO_TRADE_ENABLED=false` megtartja a manuális dashboard folyamatot,
de a setup webhook nem hoz létre automatikusan trade-et.

## Backend

```bash
cd apps/api
uv sync --all-extras --dev
uv run uvicorn smc_assistant.main:app --reload
```

Közvetlen lokális backend futtatásnál az alapértelmezett repository `memory`,
tehát nem kell futó adatbázis a gyors API fejlesztéshez. PostgreSQL módhoz:

```bash
WEBHOOK_EVENT_REPOSITORY=postgres uv run uvicorn smc_assistant.main:app --reload
```

## Frontend

```bash
cd apps/web
npm install
npm run dev
```
