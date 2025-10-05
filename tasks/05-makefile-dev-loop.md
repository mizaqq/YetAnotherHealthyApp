# Task 05 — Makefile Dev Loop

## Objective

Provide a single task runner for common developer workflows.

## Outcomes

- `Makefile` exposes: `dev`, `api-dev`, `fe-dev`, `openapi`, `codegen`, `lint`, `typecheck`, `test`, `eval-ci`, `ci`.

## Deliverables

- `Makefile` at repo root with phony targets and concise help.

## Steps

1. Create/extend Makefile

- Add targets declared in `DEVELOPER_WORK_PLAN.md` and ensure they call underlying scripts.

2. Developer ergonomics

- Ensure `make dev` starts API and FE in watch mode.
- Non-interactive defaults; clear error messages.

3. Docs

- Add brief usage notes to root `README.md`.

## Acceptance Criteria

- Running `make dev` boots FE and API locally.
- `make ci` runs full pipeline and succeeds.

## Risks & Mitigations

- Cross-platform differences: avoid Bash-isms; prefer Python/Node scripts where needed.

## Estimated Time

- 0.25 day

