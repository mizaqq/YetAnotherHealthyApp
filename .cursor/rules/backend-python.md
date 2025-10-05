## Cursor Rule: Backend (Python, FastAPI)

Applies to all backend code for the Calorie Intake Logger PoC. Optimize for correctness, clarity, and easy iteration. Prefer explicitness over magic. Follow the rules below when generating or editing backend code.

### Stack and Scope

- Python 3.11+
- FastAPI (async-first)
- Pydantic v2 models and validators
- Supabase Postgres (hosted) for persistence
- OpenSearch (Docker) for retrieval (BM25 + k-NN)
- httpx (async) for outbound HTTP
- Docker Compose for local dev

### Top-Level Principles

- Strong typing everywhere; no `Any` in public APIs.
- Separate orchestration (endpoints/services) from pure logic (normalization/calculation).
- Deterministic LLM parsing (temperature ≈ 0.2); cache by input hash.
- One source of truth for units, densities, and synonyms.
- Errors are explicit and mapped to proper HTTP status codes.

## Architecture & Conventions

### Folder Layout

Use this layout (create if missing):

```
backend/
  app/
    main.py
    deps/__init__.py          # dependency providers (auth, clients, db)
    api/
      routers/__init__.py
      routers/parse.py        # POST /api/v1/parse
      routers/match.py        # POST /api/v1/match
      routers/log.py          # POST /api/v1/log
      routers/summary.py      # GET  /api/v1/summary
      routers/foods.py        # GET  /api/v1/foods/search
    models/__init__.py        # Pydantic v2 request/response models
    services/__init__.py
    services/llm.py           # LLM orchestration (parse, clarify)
    services/retrieval.py     # OpenSearch hybrid search
    services/normalization.py # units → grams/ml, densities
    services/calculator.py    # macros calculations
    repositories/__init__.py
    repositories/meals.py     # persistence to Supabase
    clients/__init__.py
    clients/opensearch.py
    clients/supabase.py
    core/__init__.py
    core/settings.py          # pydantic-settings for env
    core/exceptions.py        # domain + HTTP error mapping
    core/logging.py           # structured logging config
```

### Settings (pydantic-settings)

- Define a single settings object loaded at startup.
- Required env vars (prefix `BACKEND_`):
  - `BACKEND_ENV` (dev|prod)
  - `BACKEND_PORT`
  - `OPENSEARCH_HOST`, `OPENSEARCH_USER`, `OPENSEARCH_PASSWORD`, `FOODS_INDEX`
  - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`
  - `CACHE_TTL_SECONDS` (parse cache)
- Do not hardcode secrets; read from env only.

### Dependency Injection

- Provide dependencies via `deps/*` using FastAPI `Depends`:
  - `get_settings()` returns immutable settings instance.
  - `get_current_user()` validates Supabase JWT and returns `{ user_id: str }`.
  - `get_opensearch()` returns a shared `OpenSearch` client with connection pooling.
  - `get_supabase()` returns a thin repository (prefer service-role key on backend).
- Close clients on shutdown events.

### Error Handling

- Raise `HTTPException` for request/authorization errors.
- Create `core/exceptions.py` for domain exceptions (e.g., `RetrievalError`, `LLMError`).
- Register exception handlers mapping domain exceptions → `HTTP 502/503/500` with clear JSON payloads:
  - `{ error: { code, message, details? } }`

### Logging

- Configure structured logging (JSON in prod, pretty in dev).
- Log one line per request with: method, path, user_id, status, latency_ms, error_code?.
- Never log secrets or full LLM prompts w/ PII.

## API Contracts (v1)

Base path: `/api/v1`.

Tags: `parse`, `match`, `log`, `summary`, `foods`.

Use Pydantic v2 models with strict types and field descriptions. Include response models and examples.

### POST /api/v1/parse

- Req: `{ text: string }`
- Res: `{ items: [{ label, quantity_expr?, grams?, ml?, confidence }], needs_clarification: boolean }`
- Behavior: deterministic parse; cache by SHA256(text). If ambiguous, set `needs_clarification`.

### POST /api/v1/match

- Req: `{ items: [{ label: string, grams: number }] }`
- Res: `{ matches: [{ label, food_id, source, source_ref?, match_score, macros_per_100g }] }`
- Behavior: OpenSearch hybrid (BM25 + k-NN) with weighted fusion; include `match_score`.

### POST /api/v1/log

- Auth: required (Supabase JWT)
- Req: `{ eaten_at?: ISODate, note?: string, items: [{ food_id, label, grams }] }`
- Res: `{ meal_id, totals: { kcal, protein_g, fat_g, carbs_g }, items: [...] }`
- Behavior: store meal and item rows; recompute totals from `macros_per_100g` at save time.

### GET /api/v1/summary?date=YYYY-MM-DD

- Auth: required
- Res: `{ date, totals: {...}, meals: [{ id, eaten_at, items: [...], totals: {...} }] }`

### GET /api/v1/foods/search?q=

- Auth: optional
- Behavior: autocomplete for manual corrections; return top N foods with labels and ids.

## Domain Services

### LLM Orchestration (`services/llm.py`)

- Use hosted LLM with temperature ≈ 0.2; timeouts and retries with jitter.
- Parsing prompt (Polish) produces JSON-only output per spec; validate with Pydantic.
- Clarification prompt produces one short question with up to 3 options.
- Cache parse results by input text hash with TTL `CACHE_TTL_SECONDS`.

### Quantity Normalization (`services/normalization.py`)

- Convert household measures → grams; ml → grams using density.
- Use a single table for unit synonyms (łyżka, łyżeczka, szklanka, plaster, kromka, garść).
- If density unknown, use category fallback; carry forward lowered `confidence`.

### Retrieval (`services/retrieval.py`)

- OpenSearch index `foods` mapping:
  - `id: keyword`
  - `name_pl: text` (Polish analyzer, edge-ngram)
  - `name_en: text` (optional)
  - `brand: keyword` (nullable)
  - `category: keyword`
  - `macros_per_100g: object { kcal, protein_g, fat_g, carbs_g }`
  - `density_g_per_ml: float` (nullable)
  - `unit_synonyms: text`
  - `source: keyword`, `source_ref: keyword`
  - `embedding: knn_vector(dim=<embedding_dim>)`
- Implement hybrid (BM25 + k-NN) and fuse scores; threshold by `match_score`.

### Calculator (`services/calculator.py`)

- Per item: `kcal = macros_per_100g.kcal * grams / 100` (same for macros).
- Per meal/day: sum items.
- Keep pure and easily testable.

## Persistence (`repositories/meals.py`)

- Use Supabase (service role) on backend.
- Abstract via a repository interface to ease switching to SQLAlchemy later.
- Batch writes where possible; validate inputs with Pydantic models.

## Security

- Supabase Auth: verify JWT with GoTrue public keys; extract `user_id`.
- Protect mutating routes; enforce per-user access in queries.
- Never trust client-sent `user_id`.

## OpenAPI/Swagger

- Document request/response schemas for all routes.
- Add descriptions for domain terms (e.g., household measures, densities).
- Provide examples for every route; group via tags.
- Consider versioned base path `/api/v1`.

## Testing (PyTest)

- Use fixtures for app, settings, clients, and repositories.
- Use `httpx.AsyncClient` for endpoint tests with `pytest.mark.anyio`.
- Parameterize tests for normalization and calculator edge cases.
- Monkeypatch LLM and OpenSearch clients; assert prompts/queries.
- Seed a tiny in-memory (or containerized) OpenSearch for retrieval tests where needed.

## Performance & Resilience

- Use async endpoints for I/O bound calls (LLM, OpenSearch, Supabase).
- Connection pooling for OpenSearch and HTTP clients.
- Background tasks for non-critical operations (e.g., logging, cache warmups).
- Timeouts and retries with exponential backoff for external calls.

## Docker & Local Dev

- Multi-stage Dockerfile (builder → runtime) for smaller images.
- Non-root user in containers.
- Compose services: `api`, `opensearch`, optionally `opensearch-dashboards`.
- Inject env via `.env` (never commit secrets).

## Coding Standards

- Type annotate all public functions and models.
- Avoid deep nesting; use guard clauses.
- Do not swallow exceptions; handle meaningfully or propagate.
- Keep comments for non-obvious rationale and invariants only.
- Match existing formatting; prefer multi-line over long one-liners.

---

### 10x Rules Mapped (FastAPI, PyTest, Postgres, Swagger, Docker)

- FastAPI
  - Use Pydantic models for request/response with strict validation.
  - Dependency injection for services and DB sessions/clients.
  - Async endpoints for I/O-bound operations; use background tasks when appropriate.
  - Proper exception handling with `HTTPException` and custom handlers.
  - Correct HTTP methods and path operation decorators.
- PyTest
  - Use fixtures for setup and DI; parameterize test inputs; monkeypatch external deps.
- Postgres
  - Connection pooling via client; use JSONB for semi-structured fields when needed.
  - Consider materialized views for heavy read-only aggregations (future).
- Swagger/OpenAPI
  - Comprehensive schemas, examples, tags, and security schemes; consider semantic versioning.
- Docker
  - Multi-stage builds; leverage layer caching; run as non-root.

---

### Project-Specific Notes

- Language is Polish for user-facing strings and clarifications; code and identifiers in English.
- Retrieval uses Polish analyzers and synonyms; maintain a curated synonyms file.
- Clarification policy: ask at most one short question, only when high impact.
- Evaluation: keep functions deterministic; enable reproducible runs over labeled set.
