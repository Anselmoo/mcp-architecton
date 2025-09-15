.PHONY: help install test lint format type-check security coverage clean all-checks
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	uv sync --dev

install-pip: ## Install dependencies using pip
	pip install -e .[dev]

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src/mcp_architecton --cov-report=term-missing

lint: ## Run linting checks
	uv run ruff check .

lint-fix: ## Run linting with auto-fixes
	uv run ruff check --fix .

format: ## Format code
	uv run ruff format .

format-check: ## Check code formatting
	uv run ruff format --check .

type-check: ## Run type checking
	uv run mypy src/mcp_architecton

security: ## Run security checks
	uv run bandit -r src/
	uv run safety check

coverage: ## Generate coverage report
	uv run pytest --cov=src/mcp_architecton --cov-report=html --cov-report=term-missing

clean: ## Clean up generated files
	rm -rf .tox/ .pytest_cache/ .coverage htmlcov/ coverage.xml *.egg-info/ build/ dist/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

pre-commit: ## Run pre-commit hooks
	uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

all-checks: lint type-check security test-cov ## Run all quality checks

tox: ## Run all tox environments
	uv run tox

tox-lint: ## Run tox lint environment
	uv run tox -e lint

tox-test: ## Run tox test environments
	uv run tox -e py310,py311,py312

tox-coverage: ## Run tox coverage environment
	uv run tox -e coverage

tox-security: ## Run tox security environment
	uv run tox -e security

dev-setup: install pre-commit-install ## Complete development setup

ci-local: all-checks ## Run CI checks locally