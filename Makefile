.PHONY: dev-up dev-down api-install api-test api-lint web-install web-dev

dev-up:
	docker compose -f infra/docker/docker-compose.yml up -d

dev-down:
	docker compose -f infra/docker/docker-compose.yml down

api-install:
	cd apps/api && python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

api-test:
	cd apps/api && . .venv/bin/activate && pytest -q

api-lint:
	cd apps/api && . .venv/bin/activate && ruff check . && mypy src

web-install:
	cd apps/web && pnpm install

web-dev:
	cd apps/web && pnpm dev
