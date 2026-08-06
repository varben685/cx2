FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/README.md ./apps/api/
COPY apps/api/src ./apps/api/src

WORKDIR /app/apps/api
RUN uv sync --locked --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "smc_assistant.main:app", "--host", "0.0.0.0", "--port", "8000"]
