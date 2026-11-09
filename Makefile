PYTHON ?= python3
VENV := .venv
PY := $(VENV)/bin/python
BASE ?=

.PHONY: bootstrap test lint typecheck forge-lint secret-scan verify build test-e2e
bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --disable-pip-version-check -r requirements-dev.txt
	npm ci --no-audit --no-fund

test:
	$(PY) -m pytest -q
	npm --prefix src/frontend run test -- --run

lint:
	$(VENV)/bin/ruff check scripts tests src/k1_studio
	npm --prefix src/frontend run lint

typecheck:
	$(VENV)/bin/mypy scripts src/k1_studio tests/forge
	npm --prefix src/frontend run typecheck

forge-lint:
	$(PY) scripts/forge_lint.py $(if $(BASE),--base "$(BASE)",)

# Requires gitleaks 8.24.2 on PATH.
secret-scan:
	gitleaks git --redact --no-banner
	gitleaks dir --redact --no-banner .

build:
	npm --prefix src/frontend run build

test-e2e:
	npm --prefix src/frontend run test:e2e

verify: test lint typecheck forge-lint
