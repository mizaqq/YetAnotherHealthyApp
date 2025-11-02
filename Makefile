ROOT_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BACKEND_DIR := $(ROOT_DIR)/apps/backend
FRONTEND_DIR := $(ROOT_DIR)/apps/frontend

.PHONY: help test test-all \
	 test-backend test-backend-unit test-backend-integration test-backend-coverage \
	 test-frontend-unit test-frontend-coverage test-frontend-watch \
	 test-frontend-e2e test-frontend-e2e-ui test-frontend-e2e-report test-frontend-e2e-codegen \
	 start-backend stop-backend

help:
	@echo "Usage: make <target>"
	@echo
	@echo "General"
	@echo "  test            Run backend and frontend unit/integration tests"
	@echo "  test-all        Run every available test suite"
	@echo
	@echo "Backend"
	@echo "  test-backend            Run full pytest suite"
	@echo "  test-backend-unit       Run backend unit tests (tests/unit)"
	@echo "  test-backend-integration Run backend integration tests (tests/integration)"
	@echo "  test-backend-coverage   Run backend tests with coverage reporting"
	@echo "  start-backend           Start backend server (development mode)"
	@echo "  stop-backend            Stop backend server"
	@echo
	@echo "Frontend"
	@echo "  test-frontend-unit      Run frontend Vitest suite"
	@echo "  test-frontend-watch     Run frontend Vitest in watch mode"
	@echo "  test-frontend-coverage  Run frontend coverage suite"
	@echo "  test-frontend-e2e       Run Playwright end-to-end tests (starts backend)"
	@echo "  test-frontend-e2e-ui    Run Playwright end-to-end tests in UI mode"
	@echo "  test-frontend-e2e-report Show the last Playwright test report"
	@echo "  test-frontend-e2e-codegen Start Playwright code generator"

test: test-backend test-frontend-unit

test-all: test-backend test-backend-coverage \
	 test-frontend-unit test-frontend-coverage test-frontend-e2e

test-backend:
	cd $(BACKEND_DIR) && APP_ENV=test uv run pytest

test-backend-unit:
	cd $(BACKEND_DIR) && APP_ENV=test uv run pytest tests/unit

test-backend-integration:
	cd $(BACKEND_DIR) && APP_ENV=test uv run pytest tests/integration

test-backend-coverage:
	cd $(BACKEND_DIR) && APP_ENV=test uv run pytest --cov=app --cov-report=term-missing

test-frontend-unit:
	npm --prefix $(FRONTEND_DIR) run test

test-frontend-watch:
	npm --prefix $(FRONTEND_DIR) run test:watch

test-frontend-coverage:
	npm --prefix $(FRONTEND_DIR) run test:coverage

start-backend:
	@echo "Starting backend server..."
	@cd $(BACKEND_DIR) && APP_ENV=development uv run uvicorn app.main:app --reload --port 8000 &
	@echo "Backend server started on port 8000"

stop-backend:
	@echo "Stopping backend server..."
	@pkill -f "uvicorn app.main:app" || true
	@echo "Backend server stopped"

test-frontend-e2e:
	@echo "Starting backend server for E2E tests..."
	@cd $(BACKEND_DIR) && APP_ENV=development uv run uvicorn app.main:app --port 8000 > /dev/null 2>&1 & echo $$! > $(ROOT_DIR)/.backend.pid
	@sleep 3
	@echo "Running E2E tests..."
	@npm --prefix $(FRONTEND_DIR) run test:e2e; \
	EXIT_CODE=$$?; \
	echo "Stopping backend server..."; \
	kill `cat $(ROOT_DIR)/.backend.pid` 2>/dev/null || true; \
	rm -f $(ROOT_DIR)/.backend.pid; \
	exit $$EXIT_CODE

test-frontend-e2e-ui:
	npm --prefix $(FRONTEND_DIR) run test:e2e:ui

test-frontend-e2e-report:
	npm --prefix $(FRONTEND_DIR) run test:e2e:report

test-frontend-e2e-codegen:
	npm --prefix $(FRONTEND_DIR) run test:e2e:codegen


