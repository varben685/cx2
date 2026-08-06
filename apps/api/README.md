# API

FastAPI backend az SMC AI Trading Assistant projekthez.

## Parancsok

```bash
uv sync --all-extras --dev
uv run uvicorn smc_assistant.main:app --reload
uv run pytest
uv run ruff check .
uv run mypy src
```

