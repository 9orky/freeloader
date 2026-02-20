PROJECT_DIR := .
SRC_DIR     := $(PROJECT_DIR)/src
TEST_DIR    := $(PROJECT_DIR)/tests

.PHONY: install install-dev install-global uninstall test test-v test-cov test-file test-k lint lint-fix fmt fmt-check check run version blocks providers secrets scratch-init scratch-plan scratch-up scratch-down scratch-clean init-home clean help

# ── Setup ────────────────────────────────────────────────────────────────────

install:
	cd $(PROJECT_DIR) && uv sync

install-dev:
	cd $(PROJECT_DIR) && uv sync --group dev

install-global:
	uv tool install -e ./$(PROJECT_DIR)

uninstall:
	uv tool uninstall freeloader

# ── Test ─────────────────────────────────────────────────────────────────────

test:
	cd $(PROJECT_DIR) && uv run pytest

test-v:
	cd $(PROJECT_DIR) && uv run pytest -v

test-cov:
	cd $(PROJECT_DIR) && uv run pytest --cov=$(SRC_DIR) --cov-report=term-missing

test-file:
	cd $(PROJECT_DIR) && uv run pytest -v $(FILE)

test-k:
	cd $(PROJECT_DIR) && uv run pytest -v -k "$(K)"

# ── Lint / Format ────────────────────────────────────────────────────────────

lint:
	cd $(PROJECT_DIR) && uv run ruff check $(SRC_DIR) $(TEST_DIR)

fmt:
	cd $(PROJECT_DIR) && uv run ruff format $(SRC_DIR) $(TEST_DIR)

fmt-check:
	cd $(PROJECT_DIR) && uv run ruff format --check $(SRC_DIR) $(TEST_DIR)

lint-fix:
	cd $(PROJECT_DIR) && uv run ruff check --fix $(SRC_DIR) $(TEST_DIR)

check: lint fmt-check test

# ── Run (without global install) ─────────────────────────────────────────────

run:
	cd $(PROJECT_DIR) && uv run fl $(ARGS)

version:
	cd $(PROJECT_DIR) && uv run fl --version

blocks:
	cd $(PROJECT_DIR) && uv run fl blocks list

providers:
	cd $(PROJECT_DIR) && uv run fl providers list

providers-check:
	cd $(PROJECT_DIR) && uv run fl providers check

secrets:
	cd $(PROJECT_DIR) && uv run fl secrets list

# ── Local deploy (dry run on a scratch project) ─────────────────────────────

scratch-dir := /tmp/fl-scratch

scratch-init:
	mkdir -p $(scratch-dir) && cd $(scratch-dir) && \
		echo '{"name":"scratch","dependencies":{}}' > package.json && \
		fl init --name scratch-app

scratch-plan:
	cd $(scratch-dir) && fl plan

scratch-up:
	cd $(scratch-dir) && fl up

scratch-down:
	cd $(scratch-dir) && fl down

scratch-clean:
	rm -rf $(scratch-dir)

# ── Housekeeping ─────────────────────────────────────────────────────────────

init-home:
	cd $(PROJECT_DIR) && uv run python -c "from freeloader.utils.paths import ensure_home; ensure_home()"

clean:
	find $(PROJECT_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find $(PROJECT_DIR) -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find $(PROJECT_DIR) -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(PROJECT_DIR)/.coverage $(PROJECT_DIR)/htmlcov

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo "Setup:"
	@echo "  make install          Install project deps"
	@echo "  make install-dev      Install with dev deps"
	@echo "  make install-global   Install fl globally on PATH (editable)"
	@echo "  make uninstall        Remove global fl"
	@echo ""
	@echo "Test:"
	@echo "  make test             Run tests (quiet)"
	@echo "  make test-v           Run tests (verbose)"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make test-file FILE=tests/test_providers.py"
	@echo "  make test-k K=coolify Run tests matching keyword"
	@echo ""
	@echo "Code quality:"
	@echo "  make lint             Ruff check"
	@echo "  make lint-fix         Ruff check with auto-fix"
	@echo "  make fmt              Ruff format"
	@echo "  make fmt-check        Ruff format (check only)"
	@echo "  make check            Lint + format-check + test"
	@echo ""
	@echo "Run:"
	@echo "  make run ARGS='blocks list'"
	@echo "  make version"
	@echo "  make blocks"
	@echo "  make providers        List providers and secrets"
	@echo "  make providers-check  Validate provider credentials"
	@echo "  make secrets          List stored secrets"
	@echo ""
	@echo "Scratch project:"
	@echo "  make scratch-init     Create /tmp/fl-scratch with fl init"
	@echo "  make scratch-plan     Run fl plan on scratch"
	@echo "  make scratch-up       Run fl up on scratch"
	@echo "  make scratch-down     Run fl down on scratch"
	@echo "  make scratch-clean    Delete scratch dir"
	@echo ""
	@echo "Housekeeping:"
	@echo "  make init-home        Create ~/.freeloader structure"
	@echo "  make clean            Remove caches and build artifacts"
