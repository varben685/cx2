.PHONY: api-test api-lint api-typecheck api-schema web-install web-test web-lint web-typecheck test lint typecheck dev docker-up

api-test:
	cd apps/api && uv run pytest

api-lint:
	cd apps/api && uv run ruff check .

api-typecheck:
	cd apps/api && uv run mypy src

api-schema:
	cd apps/api && uv run python ../../scripts/export_tradingview_schema.py

web-install:
	cd apps/web && npm install

web-test:
	cd apps/web && npm run test

web-lint:
	cd apps/web && npm run lint

web-typecheck:
	cd apps/web && npm run typecheck

test: api-test web-test

lint: api-lint web-lint

typecheck: api-typecheck web-typecheck

dev:
	docker compose up --build

docker-up:
	docker compose up --build
