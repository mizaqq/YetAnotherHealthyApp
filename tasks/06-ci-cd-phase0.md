# Task 06 — CI/CD (Phase 0)

## Objective

Add a CI pipeline that runs lint, typecheck, tests, and early evaluation with artifacts on PRs and `main`.

## Outcomes

- GitHub Actions workflow `ops/ci.yml` running `make ci`.
- Artifacts for evaluator reports.

## Deliverables

- `ops/ci.yml` with Python and Node setup, caching, and steps.
- Required status check named `ci`.

## Steps

1. Workflow

- Trigger on PRs and pushes to `main`.
- Jobs:
  - Setup Python, cache, install deps, run Python checks.
  - Setup Node, cache, install deps, run TS checks.
  - Run `make eval-ci`; upload `evaluation/reports/*` as artifacts.

2. Branch protections

- Require `ci` to pass before merging.

3. Secrets

- Configure read-only secrets if needed (e.g., for provider keys in limited environments). Prefer mocks for CI.

## Acceptance Criteria

- CI green on the main branch.
- PRs show evaluator artifacts as downloadable.

## Risks & Mitigations

- Long CI times: use caching and split jobs; run only necessary parts per change when feasible.

## Estimated Time

- 0.25–0.5 day

