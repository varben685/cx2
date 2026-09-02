# Lokális fejlesztés

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Docker Compose alatt az API `WEBHOOK_EVENT_REPOSITORY=postgres` módban indul,
így a valid TradingView webhook események a PostgreSQL `webhook_events`
táblába kerülnek.

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
