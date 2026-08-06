# Lokális fejlesztés

## Docker

```bash
cp .env.example .env
docker compose up --build
```

## Backend

```bash
cd apps/api
uv sync --all-extras --dev
uv run uvicorn smc_assistant.main:app --reload
```

## Frontend

```bash
cd apps/web
npm install
npm run dev
```

