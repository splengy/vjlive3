.PHONY: help install test lint format type-check security clean build publish

help: ## Show this help message
	@echo 'VJLive3 (The Reckoning) - Available commands:'
	@echo ''
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	@echo "Setting up pre-commit hooks..."
	pre-commit install
	@echo "Installation complete!"

test: ## Run tests with coverage
	@echo "Running tests..."
	pytest tests/ -v --cov=src/vjlive3 --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests only
	@echo "Running end-to-end tests..."
	pytest tests/e2e/ -v

test-performance: ## Run performance tests only
	@echo "Running performance tests..."
	pytest tests/performance/ -v --benchmark-only

lint: ## Run linting checks
	@echo "Running linters..."
	ruff check src/
	black --check src/
	isort --check-only src/

format: ## Auto-format code
	@echo "Formatting code..."
	black src/
	isort src/
	ruff check --fix src/

type-check: ## Run type checking
	@echo "Running type checks..."
	mypy src/

security: ## Run security scans
	@echo "Running security scans..."
	bandit -r src/
	safety check

quality: lint type-check security test ## Run all quality checks

clean: ## Clean build artifacts and caches
	@echo "Cleaning..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml .hypothesis/ .benchmarks/
	@echo "Clean complete!"

build: clean ## Build distribution packages
	@echo "Building package..."
	python -m build
	@echo "Build complete! Artifacts in dist/"

publish: ## Publish to PyPI (requires twine)
	@echo "Publishing to PyPI..."
	twine upload dist/*
	@echo "Publish complete!"

dev-setup: install ## Alias for install

run: ## Run the main application
	@echo "Starting VJLive3..."
	python -m vjlive3.main

run-debug: ## Run with debug logging
	@echo "Starting VJLive3 with debug logging..."
	LOG_LEVEL=DEBUG python -m vjlive3.main

benchmark: ## Run performance benchmarks
	@echo "Running benchmarks..."
	pytest tests/performance/ -v --benchmark-only --benchmark-storage=file://.benchmarks/

coverage-report: ## Generate HTML coverage report
	@echo "Generating coverage report..."
	pytest tests/ --cov=src/vjlive3 --cov-report=html
	@echo "Open htmlcov/index.html in your browser"

check-print-statements: ## Check for print() statements in source
	@echo "Checking for print() statements..."
	@grep -r "print(" src/ || echo "No print() statements found"

check-eval: ## Check for eval() calls in source
	@echo "Checking for eval() calls..."
	@grep -r "eval(" src/ || echo "No eval() calls found"

check-all: check-print-statements check-eval ## Run all code quality checks

.DEFAULT_GOAL := help