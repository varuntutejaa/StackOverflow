.PHONY: help backend-install backend-dev seed test lint frontend-install frontend-dev build up down

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

backend-install: ## Create venv + install backend deps
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.txt

backend-dev: ## Run FastAPI (reload) on :8000
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000

seed: ## (Re)build the database + DEMO/SIMULATED data
	cd backend && . .venv/bin/activate && python -m app.seed.seed --fresh

migrate: ## Apply Alembic migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

test: ## Run backend test suite
	cd backend && . .venv/bin/activate && pytest -q

lint: ## Ruff lint backend
	cd backend && . .venv/bin/activate && ruff check app tests

frontend-install: ## Install frontend deps
	cd frontend && npm install

frontend-dev: ## Run Next.js dev server on :3000
	cd frontend && npm run dev

build: ## Build frontend for production
	cd frontend && npm run build

up: ## docker compose up (db + redis + api)
	docker compose up --build

down: ## docker compose down
	docker compose down
