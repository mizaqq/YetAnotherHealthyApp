# Task 01a — Contracts & OpenAPI (Backend)

## Objective

Finalize API contracts and expose OpenAPI from the FastAPI app so downstream clients can integrate reliably.

## Outcomes

- Stable, versioned Pydantic models and endpoints.
- Consistent response envelope: `requestId`, `durationMs`, normalized errors.
- `docs/openapi.json` exported deterministically and kept in sync.
- Contract tests pass in CI.

## Dependencies

- Python 3.11+
- FastAPI scaffold present

## Deliverables

- `api/app/schemas/*.py` (Pydantic v2 request/response models with examples)
- Minimal routes in `api/app/main.py`: `/parse`, `/match`, `/log`, `/summary`, `/foods/search`
- OpenAPI metadata and export: `docs/openapi.json`
- Contract tests using FastAPI TestClient

## Steps

1. Define Pydantic models (requests/responses)

- Model each endpoint explicitly; add field descriptions and examples.
- Prefer composition for shared types.

2. Implement minimal routes

- Return valid example payloads (200) and standard error shape.
- Add CORS and basic logging middleware.

3. OpenAPI exposure

- Set title, version, tags, and descriptions.
- Export via `make openapi` → writes `docs/openapi.json`.

4. Contract tests

- Validate example responses against schemas using TestClient.
- Include in CI (`make ci`).

## Acceptance Criteria

- `docs/openapi.json` up‑to‑date and human‑readable.
- Example responses validate; contract tests pass in CI.

## Risks & Mitigations

- Drift between code and OpenAPI → export from running app and gate in CI.
- Over‑broad models → review with FE, iterate before wider adoption.

## PR Checklist

- [ ] Endpoints typed and documented
- [ ] `docs/openapi.json` updated via `make openapi`
- [ ] Contract tests added and passing

## Estimated Time

- ~0.5 day
