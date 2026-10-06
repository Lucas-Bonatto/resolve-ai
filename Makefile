PYTHON ?= python

.PHONY: setup dev-api dev-web test test-api test-web coverage coverage-python coverage-web lint typecheck build check reset-demo evals

setup:
	npm install
	$(PYTHON) -m pip install -e "services/api[dev]" -e packages/novapay-mcp

dev-api:
	$(PYTHON) -m uvicorn app.main:app --app-dir services/api --reload --port 8000

dev-web:
	npm run dev

test: test-api test-web

test-api:
	$(PYTHON) -m pytest services/api/tests packages/novapay-mcp/tests

test-web:
	npm test

coverage: coverage-python coverage-web

coverage-python:
	$(PYTHON) -m pytest services/api/tests packages/novapay-mcp/tests --cov=app --cov=novapay_mcp --cov-branch --cov-config=.coveragerc --cov-report=term-missing --cov-report=json

coverage-web:
	npm run test:coverage

lint:
	$(PYTHON) -m ruff check services/api packages/novapay-mcp evals scripts
	npm run lint

typecheck:
	$(PYTHON) -m mypy services/api/app packages/novapay-mcp/src
	npm run typecheck

build:
	npm run build

check: lint typecheck test build

reset-demo:
	$(PYTHON) scripts/reset_demo.py

evals:
	$(PYTHON) evals/run_local.py
