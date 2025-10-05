.PHONY: help install sync dev openapi test lint format clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install   - Install backend dependencies (alias for sync)"
	@echo "  sync      - Sync backend dependencies using uv"
	@echo "  dev       - Run backend development server"
	@echo "  openapi   - Export OpenAPI schema to docs/openapi.json"
	@echo "  test      - Run backend tests"
	@echo "  lint      - Run linter (ruff)"
	@echo "  format    - Format code (ruff)"
	@echo "  clean     - Remove generated files"
	@echo "  ci        - Run CI checks (lint + test)"

# Sync dependencies with uv
sync:
	cd api && uv sync

# Install dependencies (alias for sync)
install: sync

# Run development server
dev:
	cd api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Export OpenAPI schema
openapi:
	cd api && uv run python -m app.scripts.export_openapi

# Run tests
test:
	cd api && uv run pytest -v

# Lint code
lint:
	cd api && uv run ruff check .

# Format code
format:
	cd api && uv run ruff format .

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# CI checks
ci: lint test
