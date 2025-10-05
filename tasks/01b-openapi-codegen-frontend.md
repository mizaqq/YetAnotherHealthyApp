# Task 01b — OpenAPI Codegen & Client (Frontend)

## Objective

Generate TypeScript types and a typed API client from OpenAPI and integrate with a thin fetch wrapper.

## Outcomes

- Generated types/client under `frontend/src/lib/api/`.
- Centralized API wrapper for base URL, JWT, timeouts, and error normalization.
- FE compiles using only generated types; no hand‑rolled DTOs.

## Dependencies

- Node 20+
- `docs/openapi.json` available (exported by backend)

## Deliverables

- Codegen artifacts in `frontend/src/lib/api/`
- API wrapper module (e.g., `frontend/src/lib/api/client.ts`)

## Steps

1. Codegen

- Run `make codegen` to invoke `openapi-typescript` (types) and `openapi-fetch` or `orval` (client).
- Commit generated files.

2. API wrapper

- Implement a small wrapper for base URL, JWT injection, timeouts, and error mapping.

3. Integration

- Replace one sample call to use the generated client and types end‑to‑end.
- Ensure `tsc --noEmit` passes.

## Acceptance Criteria

- FE builds with only generated types for API calls.
- Typecheck (`tsc --noEmit`) passes.

## Risks & Mitigations

- Spec drift → run `make openapi` + `make codegen` in CI and on PRs.
- Client ergonomics → use wrapper for consistent ergonomics without editing generated code.

## PR Checklist

- [ ] `frontend/src/lib/api/*` generated and committed
- [ ] Wrapper added and used in at least one call site
- [ ] CI typecheck/lint pass

## Estimated Time

- ~0.5 day
