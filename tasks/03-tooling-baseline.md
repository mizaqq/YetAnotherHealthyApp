# Task 03 — Tooling Baseline (Python + TypeScript)

## Objective

Establish linting, formatting, typechecking, testing, and pre‑commit hooks for consistent developer experience.

## Outcomes

- One‑command checks: `make lint`, `make typecheck`, `make test`, `make ci`.
- Pre‑commit enforces cleanliness on changed files.

## Deliverables

- Python: ruff, mypy, pytest (+ coverage) configs.
- TS: eslint, prettier, tsc, vitest configs.
- Pre‑commit config and base repo configs: `.editorconfig`, `.gitattributes`, `.gitignore`.

## Steps

1. Python stack

- Add `pyproject.toml` with ruff, pytest, mypy config.
- Configure coverage thresholds; structure tests under `api/tests/`.

2. TypeScript stack

- Add eslint + prettier configs; `tsconfig.json` for strict mode.
- Setup `vitest` for unit tests under `frontend/src/__tests__/`.

3. Pre‑commit

- Hooks: ruff, isort (if used), mypy (changed), eslint, prettier.

4. Make targets

- Ensure `make lint`, `make typecheck`, `make test`, `make ci` are wired.

## Acceptance Criteria

- `make ci` succeeds locally on a clean checkout.
- Pre‑commit passes on staged changes.

## Risks & Mitigations

- Slow CI: cache dependencies; run partial checks per project where possible.

## Estimated Time

- 0.5 day

