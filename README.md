# SMC AI Trading Assistant

Az `smc-ai-trading-assistant` egy SMC/ICT-inspired trading setup elemző és
AI-támogatott kereskedési asszisztens. A cél nem profitgarancia, hanem a
kereskedési döntések következetesebb, mérhetőbb, visszatesztelhetőbb és
tanulhatóbb kezelése.

## Jelenlegi állapot

Phase 0 bootstrap készült el:

- FastAPI backend `/health` és `/ready` végponttal.
- React/Vite frontend minimális státuszoldallal.
- PostgreSQL-t tartalmazó Docker Compose konfiguráció.
- Dokumentációs struktúra, ExecPlan és első learning dokumentum.
- Alap lint, type check és teszt konfiguráció.

## Gyors indítás

```bash
cp .env.example .env
docker compose up --build
```

Ezután:

- Backend: [http://localhost:8000/health](http://localhost:8000/health)
- Frontend: [http://localhost:5173](http://localhost:5173)

## Lokális fejlesztés

Backend:

```bash
cd apps/api
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run mypy src
uv run uvicorn smc_assistant.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run test
npm run lint
npm run typecheck
npm run dev
```

## Fontos dokumentumok

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/index.md](docs/index.md)
- [docs/PLANS.md](docs/PLANS.md)
- [docs/exec-plans/active/full-project.md](docs/exec-plans/active/full-project.md)
- [docs/learning/phase-00-bootstrap.md](docs/learning/phase-00-bootstrap.md)

