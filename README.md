## YetAnotherHealthyApp

![Status - WIP](https://img.shields.io/badge/status-WIP-yellow) ![Version - 0.1.0](https://img.shields.io/badge/version-0.1.0-blue) ![License - TBD](https://img.shields.io/badge/license-TBD-lightgrey)

Quick meal logging and macro tracking with AI-assisted parsing of free‑text meal descriptions.

## Table of Contents

- [Project description](#project-description)
- [Tech stack](#tech-stack)
- [Getting started locally](#getting-started-locally)
- [Available scripts](#available-scripts)
- [Project scope](#project-scope)
- [Project status](#project-status)
- [License](#license)

## Project description

YetAnotherHealthyApp is a web app for users who consciously manage their diet and want a fast way to record meals and track calories and macronutrients. The MVP focuses on:

- Free‑text meal input with support for common local units (g, ml, pcs, slice, tablespoon, cup),
- AI analysis mapping parsed ingredients to a canonical product list (informed by Open Food Facts) and estimating macros,
- Clear visualization of totals and ingredients, with the ability to edit and re‑run analysis,
- History and reporting against a user‑defined daily calorie goal.

Data is stored per user with row‑level security (RLS) in Supabase. The primary MVP priority is the reliability and clarity of macro calculations.

## Tech stack

- **Frontend — React 19 (Vite, TypeScript 5, Tailwind CSS 4, shadcn/ui)**
  - SPA built with Vite for fast DX.
  - Source in `apps/frontend/src`, browser clients in `apps/frontend/src/lib`, build output in `apps/frontend/dist`.
  - Tooling config: `apps/frontend/vite.config.ts`, `apps/frontend/tailwind.config.js`, `apps/frontend/eslint.config.js`, `apps/frontend/tsconfig.json`.
- **Backend — FastAPI 0.119.0 (Python 3.13)**
  - REST API service with app entrypoint at `apps/backend/app/main.py`.
  - API routes under `apps/backend/app/api/v1/` (e.g., `endpoints/health.py`).
  - Settings/infrastructure in `apps/backend/app/core/` (e.g., `config.py` reads `.env`).
  - Domain/services in `apps/backend/app/services/`; models/schemas in `apps/backend/app/models/` and `apps/backend/app/schemas/`.
  - Dependencies: `fastapi[standard]`, `pydantic-settings`; dev tooling: `ruff`.
- **Testing & Quality Assurance**
  - **Frontend**: Vitest + React Testing Library (unit tests), MSW (API mocking), Playwright (E2E tests), axe-core (accessibility), ESLint (linting), TypeScript (type checking).
  - **Backend**: pytest (unit/integration tests), FastAPI TestClient/httpx (API tests), respx/pytest-httpx (HTTP mocking), Schemathesis (contract tests), Ruff (linting/formatting), pytest-cov (coverage).
  - **Performance**: k6 (load testing), Lighthouse (UI performance metrics), Coveralls/Codecov (coverage reporting).
- **AI — via OpenRouter (planned)**
  - Centralized access to multiple model providers with API key and cost controls.
  - Integration is intended in backend services, configured via environment variables.
- **CI/CD & Hosting (planned)**
  - GitHub Actions for CI with test matrix (linting, unit, integration, contract, E2E tests), optional Docker images, DigitalOcean for hosting.

Repository layout:

- `apps/frontend` — React web client
- `apps/backend` — FastAPI API service
- `.ai/` — product docs (e.g., PRD, tech stack)
- `apps/README.md` — app-level docs

## Getting started locally

### Prerequisites

- Node.js 18+ (20+ recommended) and npm
- Python 3.13+
- Optional but recommended: `uv` for Python dependency management

### Frontend (Vite dev server)

```bash
cd apps/frontend
npm install
npm run dev
# App serves at http://localhost:5173
```

### Backend (FastAPI)

Using uv (recommended):

```bash
cd apps/backend
uv sync
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000
# API serves at http://localhost:8000
```

Using pip (alternative):

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install --upgrade pip
pip install "fastapi[standard]>=0.119.0" "pydantic-settings>=2.6.1"
fastapi dev app/main.py --host 0.0.0.0 --port 8000
```

### Verify the API

Health endpoint:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok"}
```

CORS is preconfigured for Vite dev origins at `http://localhost:5173` and `http://127.0.0.1:5173`.

### Environment variables

The backend reads environment variables from `.env` (via `pydantic-settings`) in `apps/backend`.
No secrets are required to run the health check; AI keys and Supabase config will be added as features are implemented.

## Available scripts

### Frontend (`apps/frontend/package.json`)

- **dev**: start Vite dev server
- **build**: production build
- **preview**: preview the production build locally
- **typecheck**: run TypeScript without emitting files
- **lint**: ESLint with zero warnings allowed

### Backend

- **Run (dev)**: `fastapi dev app/main.py` (or `uv run fastapi dev app/main.py`)
- **Run (prod)**: `fastapi run app/main.py`
- **Lint**: if using uv — `uv run ruff check app` and `uv run ruff format app`

## Project scope

### In scope (MVP)

- Authentication with Supabase (email/password), password policy, session handling, secure logout; per-user data isolation via RLS.
- Add meals with category selection (breakfast, second breakfast, lunch, afternoon snack, dinner) and free‑text description supporting units: g, ml, pcs, slice, tablespoon, cup. Defaults for units are indicated and can be overridden.
- AI analysis pipeline that parses ingredients, maps them to a canonical product list (Open Food Facts + model knowledge), and returns structured JSON with per‑ingredient and total macros; confidence threshold ≥ 0.8 yields canonical product IDs.
- Edit and confirm results; re-run analysis after edits; keep edit history and note defaults used.
- Manual mode for direct calories/protein/fat/carbs input with validation; manual entries clearly marked and convertible to AI later.
- History and reporting: daily list with filters, daily progress bar against goal, 7‑day trend chart; all times in server timezone.
- User settings: onboarding to set daily calorie goal; update goal and unit preferences later; changes reflected in reports.
- Observability: log AI calls with success/error and retries; mark manual corrections for quality analysis.

### Out of scope (MVP)

- Media uploads (e.g., meal photos).
- Sharing meals or social features.
- Native mobile apps (web only for MVP).
- Real‑time Open Food Facts updates (post‑MVP updates instead).
- Response caching or RAG.

## Project status

- Version: 0.1.0 (monorepo scaffold in progress).
- Implemented: FastAPI service with `/api/v1/health`, React + Vite scaffold, CORS configured for local dev.
- Planned next: Supabase integration with RLS, AI analysis via OpenRouter, history/views, settings with goals, reporting.
- Performance and quality targets (from PRD): 95% AI responses ≤ 12s; ≥ 75% AI proposals accepted (after edits) in sample of 200; 99% RLS isolation success.

Additional documentation:

- Product Requirements (PRD): `.ai/prd.md`
- Tech stack and structure: `.ai/tech-stack.md`
- Apps overview: `apps/README.md`

## License

License is not specified yet. Until a license is added, all rights are reserved. If you plan to contribute or use this project, please open an issue to discuss the intended license.
