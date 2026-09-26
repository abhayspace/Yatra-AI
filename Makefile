# Common tasks. Requires Python 3.12+ and (for the frontend targets) Node 22.
PY ?= python3
VENV ?= .venv
BIN := $(VENV)/bin

.PHONY: setup test eval eval-live frontend-check up down

setup:                       ## create the virtualenv and install pinned dependencies
	$(PY) -m venv $(VENV)
	$(BIN)/pip install -q -r requirements-dev.txt -c constraints.txt

test: setup                  ## offline suite: no network, no credentials
	$(BIN)/pytest -q

eval: setup                  ## trajectory evals with the scripted model (fast)
	$(BIN)/python -m evals.run_evals

eval-live: setup             ## trajectory evals + LLM judge on the real Azure AI Foundry deployment
	YATRA_LIVE=1 $(BIN)/python -m evals.run_evals --live --judge

frontend-check:              ## type-check, lint and build the frontend
	cd frontend && npm ci && npx tsc --noEmit && npm run lint && npm run build

up:                          ## run backend + frontend containers (needs .env)
	docker compose up --build

down:
	docker compose down
