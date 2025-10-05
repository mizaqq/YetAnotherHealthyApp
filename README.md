# YetAnotherHealthyApp

**Calorie Intake Logger** — A Polish-language web app PoC that estimates daily calorie and macro intake from free-text descriptions using LLM-powered parsing and RAG retrieval over a food database.

---

## Overview

This project uses a **hosted LLM** to parse Polish text into raw ingredients and quantities, then performs **hybrid retrieval** (full-text + vector) over a food database in Supabase Postgres (`pgvector`) to ground calculations in per-100g nutrition facts. Users authenticate via **Supabase Auth**, can edit/delete logged meals, and view daily totals.

**Phase 0 Focus:** Contracts-first development, LLM hardening, tooling baseline, and early evaluation on 20 labeled meals.

---

## Quick Start

### Prerequisites

- **Python 3.11+**
- **Node 20+** (use `.nvmrc`)
- **Supabase project** with credentials in `.env`
- **LLM API key** (OpenAI or compatible)

### Setup

1. Clone and enter the repository:

   ```bash
   cd YetAnotherHealthyApp
   ```

2. Copy environment template:

   ```bash
   cp .env.example .env
   # Edit .env with your Supabase and LLM credentials
   ```

3. Install dependencies:

   ```bash
   make install-api
   make install-fe
   ```

4. Run development servers:
   ```bash
   # In separate terminals:
   make api-dev    # FastAPI on :8000
   make fe-dev     # Next.js on :3000
   ```

---

## Project Structure

```
YetAnotherHealthyApp/
├── Root Configuration
│   ├── Makefile                    # Single task runner
│   ├── .gitignore                  # Git ignore patterns
│   ├── .editorconfig               # Editor configuration
│   ├── .gitattributes              # Git attributes
│   ├── .pre-commit-config.yaml     # Pre-commit hooks
│   ├── .nvmrc                      # Node version (20)
│   ├── .python-version             # Python version (3.11)
│   └── docker-compose.yml          # Local dev orchestration
│
├── api/                            # FastAPI Backend
│   ├── pyproject.toml              # Python project config (ruff, mypy, pytest)
│   ├── Dockerfile                  # Multi-stage Docker build
│   ├── prompts/                    # Versioned LLM prompts
│   │   ├── parse_v1.txt            # Text → items parsing prompt
│   │   └── clarify_v1.txt          # Clarification question prompt
│   ├── app/
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── deps/                   # Dependency injection providers
│   │   ├── api/routers/            # API endpoints (v1)
│   │   │   ├── parse.py            # POST /api/v1/parse
│   │   │   ├── match.py            # POST /api/v1/match
│   │   │   ├── log.py              # POST /api/v1/log
│   │   │   ├── summary.py          # GET /api/v1/summary
│   │   │   └── foods.py            # GET /api/v1/foods/search
│   │   ├── models/                 # Pydantic v2 request/response models
│   │   ├── services/               # Domain services
│   │   │   ├── llm.py              # LLM orchestration (parse, clarify)
│   │   │   ├── retrieval.py        # Postgres FTS + pgvector hybrid search
│   │   │   ├── normalization.py    # Units → grams/ml conversion
│   │   │   └── calculator.py       # Macros calculations
│   │   ├── repositories/           # Data persistence layer
│   │   │   └── meals.py            # Meal storage via Supabase
│   │   ├── clients/                # External service clients
│   │   │   └── supabase.py         # Supabase client wrapper
│   │   ├── core/                   # Core configuration
│   │   │   ├── settings.py         # Pydantic-settings (env vars)
│   │   │   ├── exceptions.py       # Domain + HTTP error mapping
│   │   │   └── logging.py          # Structured logging setup
│   │   └── scripts/
│   │       └── export_openapi.py   # OpenAPI spec export script
│   └── tests/
│       ├── conftest.py             # PyTest fixtures
│       ├── test_main.py            # Main app tests
│       └── llm_golden/             # Golden tests for LLM outputs
│
├── frontend/                       # Next.js Frontend
│   ├── package.json                # Node dependencies + scripts
│   ├── tsconfig.json               # TypeScript configuration
│   ├── next.config.js              # Next.js configuration
│   ├── .eslintrc.json              # ESLint rules
│   ├── .prettierrc                 # Prettier formatting
│   ├── Dockerfile                  # Frontend container build
│   └── src/
│       ├── app/                    # Next.js App Router
│       │   ├── layout.tsx          # Root layout
│       │   └── page.tsx            # Home page
│       ├── lib/api/                # Generated API client (codegen)
│       ├── components/             # React components
│       └── hooks/                  # Custom React hooks
│
├── evaluation/                     # Early Evaluation System
│   ├── dataset.dev.jsonl           # 20 labeled meals for testing
│   ├── run_eval.py                 # Evaluator script (MAE, accuracy)
│   └── reports/                    # Generated evaluation reports
│
├── docs/                           # Documentation
│   └── openapi.json                # Generated OpenAPI spec (from API)
│
├── ingestion/                      # Optional in Phase 0
│   └── (seed data + ingestion scripts)
│
└── ops/                            # CI/CD
    └── ci.yml                      # GitHub Actions workflow
```

---

## Development Workflow

### Available Make Commands

Run `make help` to see all available commands:

```bash
make install-api      # Install API dependencies
make install-fe       # Install frontend dependencies
make api-dev          # Run FastAPI with hot reload (port 8000)
make fe-dev           # Run Next.js dev server (port 3000)
make openapi          # Export OpenAPI spec to docs/openapi.json
make codegen          # Generate FE types/client from OpenAPI
make lint             # Run linters (ruff + eslint)
make typecheck        # Run type checkers (mypy + tsc)
make test             # Run tests (pytest + vitest)
make eval-ci          # Run evaluator on dataset
make ci               # Full CI pipeline (lint + typecheck + test + eval)
make clean            # Remove build artifacts and caches
```

### Typical Development Loop

1. **Make changes** to API models/endpoints
2. **Export OpenAPI spec**: `make openapi`
3. **Generate frontend client**: `make codegen`
4. **Run quality checks**: `make lint typecheck test`
5. **Commit** (pre-commit hooks will run automatically)

### Contract-First Development

1. Define/update Pydantic models in `api/app/models/`
2. Implement endpoint in `api/app/api/routers/`
3. Export OpenAPI: `make openapi`
4. Generate frontend types: `make codegen`
5. Frontend now has type-safe client for the new endpoint

---

## Tech Stack

### Backend

- **FastAPI** (async, Python 3.11+)
- **Pydantic v2** (request/response validation)
- **Supabase** (Postgres with pgvector, Auth)
- **httpx** (async HTTP client)
- **pytest** (testing framework)
- **ruff** (linting + formatting)
- **mypy** (type checking)

### Frontend

- **Next.js 14+** (App Router)
- **TypeScript**
- **pnpm** (package manager)
- **openapi-typescript** (type generation)
- **ESLint + Prettier** (linting + formatting)

### LLM & Retrieval

- **OpenAI API** (or compatible, configurable)
- **Postgres FTS** (Polish full-text search)
- **pgvector** (semantic similarity search)
- **Hybrid retrieval** (BM25-style + k-NN fusion)

### Tooling

- **Makefile** (single task runner)
- **Pre-commit hooks** (ruff, mypy, eslint, prettier)
- **GitHub Actions** (CI/CD in `ops/ci.yml`)
- **Docker + Docker Compose** (local development)

## Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# Backend Configuration
BACKEND_ENV=dev
BACKEND_PORT=8000

# Supabase
BACKEND_SUPABASE_URL=https://your-project.supabase.co
BACKEND_SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# LLM Provider
BACKEND_LLM_PROVIDER=openai
BACKEND_LLM_MODEL=gpt-4o-mini
BACKEND_LLM_API_KEY=sk-...
BACKEND_LLM_TEMPERATURE=0.2
BACKEND_LLM_TIMEOUT_SECONDS=30

# Cache
BACKEND_CACHE_TTL_SECONDS=3600

# Logging
BACKEND_LOG_LEVEL=INFO
```

---

## Testing

### Run All Tests

```bash
make test
```

### Backend Tests Only

```bash
cd api && pytest
```

### Frontend Tests Only

```bash
cd frontend && pnpm test
```

### Golden Tests (LLM)

Golden tests ensure deterministic LLM outputs:

```bash
cd api && pytest tests/llm_golden/
```

---

## Evaluation

Run the evaluator on the 20-meal development dataset:

```bash
make eval-ci
```

This computes:

- **MAE** (Mean Absolute Error) for kcal and macros
- **Top-1 retrieval accuracy** (pgvector + FTS)
- **Clarification rate**

Reports are saved to `evaluation/reports/`.

---

## CI/CD

GitHub Actions workflow in `ops/ci.yml`:

- **Triggers:** PRs and pushes to `main`
- **Jobs:**
  - Lint + typecheck (Python + TypeScript)
  - Unit tests (pytest + vitest)
  - Evaluator run (artifacts uploaded)
- **Required checks:** All must pass before merge

---

## Contributing

1. Follow `.editorconfig` and pre-commit hooks
2. Use **Study Mode** (`TODO (User):`) for learning implementations
3. Keep PRs small and focused
4. Ensure `make ci` passes before pushing
5. Update OpenAPI spec when changing contracts

---

## Documentation

- **[Project Description](./project_description.md)** — Detailed product spec
- **[Developer Work Plan](./DEVELOPER_WORK_PLAN.md)** — Phase 0 implementation plan
- **[Engineering Rules](./.cursor/rules/engineering-overall.md)** — General coding standards
- **[Backend Rules](./.cursor/rules/backend-python.md)** — Python/FastAPI conventions
- **Tasks** — See `tasks/` directory for phase breakdowns

---

## License

Internal PoC — Not licensed for public use.
