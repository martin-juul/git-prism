.PHONY: help install dev-install build test test-cov lint fmt typecheck check clean ci publish publish-test

# Detect if uv is available, fallback to standard tools
UV := $(shell command -v uv 2> /dev/null)
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
ACTIVATE := $(VENV)/bin/activate

ifeq ($(UV),)
    # Use venv/pip
    PIP_INSTALL := $(BIN)/pip install -e ".[dev]"
    PIP_CMD := $(BIN)/pip
    PYTHON_CMD := $(BIN)/python
    PYTEST_CMD := $(BIN)/pytest
    RUFF_CMD := $(BIN)/ruff
    MYPY_CMD := $(BIN)/mypy
else
    # Use uv
    PIP_INSTALL := uv pip install -e ".[dev]"
    PIP_CMD := uv pip
    PYTHON_CMD := $(BIN)/python
    PYTEST_CMD := uv run pytest
    RUFF_CMD := uv run ruff
    MYPY_CMD := uv run mypy
endif

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: ## Initialize development environment (auto-detects uv or falls back to venv)
	@echo "Setting up development environment..."
ifeq ($(UV),)
	@echo "Using standard venv (uv not found)"
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip setuptools wheel
	$(PIP_INSTALL)
else
	@echo "Using uv (fast)"
	uv venv
	$(PIP_INSTALL)
endif
	@echo ""
	@echo "Setup complete! Activate with:"
	@echo "  source $(VENV)/bin/activate"

install: ## Install the package
ifeq ($(UV),)
	$(PYTHON) -m pip install -e .
else
	uv pip install -e .
endif

dev-install: ## Install in development mode with dev dependencies
	$(PIP_INSTALL)

sync: ## Sync dependencies (uv only, creates lockfile)
ifeq ($(UV),)
	@echo "uv is required for 'make sync'. Install from: https://astral.sh/uv"
	@exit 1
else
	uv pip compile pyproject.toml -o requirements.txt
	uv pip sync requirements.txt
endif

lock: ## Generate/update uv.lock file
ifeq ($(UV),)
	@echo "uv is required for 'make lock'. Install from: https://astral.sh/uv"
	@exit 1
else
	uv lock
endif

build: ## Build the package (wheel/source)
ifeq ($(UV),)
	$(PYTHON) -m build
else
	uv build
endif

build-deps: ## Install build dependencies
ifeq ($(UV),)
	$(PIP_CMD) install -e ".[build]"
else
	uv pip install -e ".[build]"
endif

publish-clean: ## Clean dist directory before publishing
	rm -rf dist/
	$(MAKE) build

publish-deps: ## Install publishing dependencies (twine, build tools)
ifeq ($(UV),)
	$(PIP_CMD) install -e ".[build]"
else
	uv pip install -e ".[build]"
endif

publish-test: publish-deps ## Upload to TestPyPI (for testing before production)
	@echo "Uploading to TestPyPI..."
	$(PYTHON) -m twine upload --repository testpypi dist/*
	@echo ""
	@echo "Test with: uv pip install --index-url https://test.pypi.org/simple/ git-prism"

publish: publish-deps ## Upload to PyPI (production)
	@echo "Uploading to PyPI..."
	@echo "Make sure you have:"
	@echo "  1. A PyPI account at https://pypi.org/account/register/"
	@echo "  2. An API token at https://pypi.org/manage/account/token/"
	@echo "  3. Token saved in ~/.pypirc"
	@echo ""
	@read -p "Press Enter to continue or Ctrl+C to cancel..."
	$(PYTHON) -m twine upload dist/*
	@echo ""
	@echo "Published successfully! Install with: uv pip install git-prism"

test: ## Run all tests
	$(PYTEST_CMD) tests/

test-cov: ## Run tests with coverage report
ifeq ($(UV),)
	$(BIN)/pytest --cov=git_prism --cov-report=html --cov-report=term
else
	uv run pytest --cov=git_prism --cov-report=html --cov-report=term
endif

test-unit: ## Run only unit tests
	$(PYTEST_CMD) tests/ -m unit

test-integration: ## Run only integration tests
	$(PYTEST_CMD) tests/ -m integration

test-verbose: ## Run tests with verbose output
	$(PYTEST_CMD) -v

lint: ## Check code with ruff
	$(RUFF_CMD) check src tests

fmt: ## Format code with ruff
	$(RUFF_CMD) format src tests

fmt-check: ## Check if code is formatted
	$(RUFF_CMD) format --check src tests

typecheck: ## Run type checking with mypy
	$(MYPY_CMD) src/git_prism

check: lint fmt-check typecheck ## Run all quality checks (lint, format, typecheck)

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

venv: ## Create virtual environment (uses venv)
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip setuptools wheel

run: ## Run git-prism CLI (use: make run ARGS="analyze . -o output")
ifeq ($(UV),)
	$(PYTHON_CMD) -m git_prism.cli $(ARGS)
else
	uv run git-prism $(ARGS)
endif

run-analyze: ## Run analyze command on current directory
ifeq ($(UV),)
	$(PYTHON_CMD) -m git_prism.cli analyze .
else
	uv run git-prism analyze .
endif

run-help: ## Show help for the CLI
ifeq ($(UV),)
	$(PYTHON_CMD) -m git_prism.cli --help
else
	uv run git-prism --help
endif

# Install uv command (helper)
install-uv: ## Install uv (fast Python package manager)
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "uv installed! Run 'make init' to set up the project."

update-deps: ## Update dependencies to latest versions
ifeq ($(UV),)
	@echo "uv is required. Run 'make install-uv' first."
	@exit 1
else
	uv pip upgrade --all
endif

ci: ## CI pipeline: install deps, lint, test, build
	@echo "=== Running CI Pipeline ==="
	@echo ""
	@echo "Step 1: Installing dependencies..."
ifeq ($(UV),)
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv $(VENV); \
		$(BIN)/pip install --upgrade pip setuptools wheel; \
	fi
	$(PIP_INSTALL)
else
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment with uv..."; \
		uv venv; \
	fi
	$(PIP_INSTALL)
endif
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Step 2: Running linter..."
	$(RUFF_CMD) check src tests
	@echo "✓ Linting passed"
	@echo ""
	@echo "Step 3: Running type checker..."
	$(MYPY_CMD) src/git_prism
	@echo "✓ Type checking passed"
	@echo ""
	@echo "Step 4: Running tests..."
	$(PYTEST_CMD) tests/ -q
	@echo "✓ Tests passed"
	@echo ""
	@echo "Step 5: Building package..."
	$(MAKE) build
	@echo ""
	@echo "=== CI Pipeline Complete ==="
