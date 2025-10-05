## Cursor Rule: Engineering (All)

Applies to all code in this repository (backend and frontend). Optimize for correctness, clarity, and maintainability. Prefer explicitness over cleverness. These rules complement stack-specific ones in `backend-python.md` and `frontend-typescript.md`.

### Scope

- All services, libraries, scripts, and tests
- Both runtime code and developer tooling/configuration

### Top-Level Principles

- Strong typing and explicit boundaries; no unsafe types in public APIs
- Small, composable modules; pure logic separated from I/O and orchestration
- Fail fast with meaningful errors; never swallow exceptions
- Security and privacy by default; never log secrets or tokens
- Deterministic behavior and reproducible results where feasible
- Observability baked in: structured logs, useful error messages

## Study Mode (User Learning)

Use Study Mode when introducing key functionality the user wants to implement themselves. The assistant should scaffold structure and contracts, but leave core logic for the user, marking the exact place for user code with the following marker:

`TODO (User):`

### Rules

- Provide full scaffolds: imports, types/interfaces, function/class signatures, docstrings/tsdoc, and error contracts.
- Leave core logic empty and add a clear inline marker comment at the insertion point.
- Ensure code compiles/builds: use placeholders that fail fast at runtime if executed.
  - Python: `raise NotImplementedError("User implementation required")`
  - TypeScript: `throw new Error("User implementation required")`
- Keep surfaces deterministic and testable; wire dependencies via parameters or DI.
- Tests may be scaffolded but should be skipped/pending until user completes logic.
  - Python: `@pytest.mark.skip("Waiting for user implementation")`
  - Jest: `test.skip(...)` or `it.todo(...)`
- Study Mode is allowed in WIP branches; it must be fully implemented before merging to main.

### Examples

Python function scaffold:

```python
def calculate_macros(grams: float, macros_per_100g: dict[str, float]) -> dict[str, float]:
    """Return kcal/protein/fat/carbs for given grams.

    Args:
        grams: Ingredient weight in grams.
        macros_per_100g: Keys: "kcal", "protein_g", "fat_g", "carbs_g".
    Returns:
        Per-item macros for the specified grams.
    """
    # TODO (User):
    raise NotImplementedError("User implementation required")
```

TypeScript function scaffold:

```ts
export type Macros = {
  kcal: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
};

export function calculateMacros(grams: number, per100g: Macros): Macros {
  //TODO (User):
  throw new Error("User implementation required");
}
```

## Cross-Cutting Coding Practices

### Structure & Separation

- Keep functions short and single-purpose; prefer guard clauses over deep nesting
- Separate orchestration (controllers/components) from domain/pure logic
- Encapsulate external dependencies behind interfaces/clients
- Centralize configuration in settings; no hardcoded secrets

### Types & Contracts

- Explicit return types for public functions/APIs
- Avoid `any`/untyped values in exported surfaces
- Validate all external inputs at boundaries; validate and sanitize before use
- Keep shared request/response types consistent across backend and frontend

### Naming & Readability

- Use descriptive, intention-revealing names (functions: verbs, variables: nouns)
- Avoid abbreviations and cryptic short names
- Comments only for non-obvious rationale, invariants, or caveats
- Match existing formatting; prefer multi-line over hard-to-read one-liners

### Error Handling & Logging

- Do not catch errors without handling or rethrowing with context
- Map domain errors to user-meaningful messages; keep technical details in logs
- Structured logging (pretty in dev, JSON in prod); never log PII/secrets

### Security & Privacy

- Enforce authentication/authorization on protected operations
- Input validation and output encoding; avoid injection risks
- Principle of least privilege for tokens/keys; rotate and store in env only
- Avoid storing tokens in browser storage; prefer memory/session as appropriate

### Performance & Resilience

- Use async/non-blocking I/O for network-bound work
- Timeouts, retries with backoff, and circuit-breaker behavior for external calls
- Memoize/cache where it materially improves UX or cost, with clear TTLs

## Testing Policy (All Code Must Be Tested)

### Testing Pyramid

- Unit tests: fast, isolated, deterministic for pure logic and small units
- Integration tests: realistic boundaries (HTTP, DB, search, auth) via test doubles or containers as needed
- End-to-end (E2E): critical user flows only; keep stable and value-focused

### Standards

- Follow AAA (Arrange-Act-Assert) and Given-When-Then naming
- Each bug fix includes a regression test
- Avoid brittle assertions; prefer behavior over implementation details
- Minimize snapshot tests; use them only when structure itself is the contract

### Tooling (align with stack rules)

- Backend: PyTest; `httpx.AsyncClient` for API tests; fixtures/mocking for external deps
- Frontend: Jest + Testing Library for units; Playwright for E2E core journeys

### Coverage & Quality Gates

- New/changed code includes tests; no net reduction of meaningful coverage
- Target coverage: ~80% lines and ~70% branches overall, with focus on critical paths
- All tests must pass locally and in CI before merge

## CI/CD Quality Gates

- Lint, type-check, and format checks must pass (no warnings in CI)
- Build succeeds without errors; bundles/images are free of obvious bloat
- Security checks (dependency audit, basic SAST/lint rules) pass
- No Study Mode markers remain: `TODO (User):` must be absent in main

## Definition of Done (DoD)

- Acceptance criteria met; feature flags/toggles applied if appropriate
- Public contracts stable and documented (OpenAPI/types updated, examples added)
- Code follows these rules and stack-specific guidelines
- Tests written/updated:
  - Unit tests for pure logic and edge cases
  - Integration/E2E tests for critical flow impact
  - All tests green locally and in CI
- Quality gates pass:
  - Lint and type checks clean
  - Coverage targets respected (no regressions on critical modules)
- Observability in place: meaningful logs and error messages (no secrets)
- Security reviewed: inputs validated, authz/authn enforced, secrets handled via env
- Documentation updated: README/usage notes, env vars, migrations, runbooks as needed
- Peer review completed and approvals collected
- CI pipeline green on the merge target branch
- No Study Mode markers remain; user areas implemented and tested

## Pull Request Guidelines

- Keep PRs small and focused; separate refactors from feature changes
- Write clear descriptions: problem, approach, trade-offs, screenshots for UI changes
- Include test evidence (commands, coverage, or E2E trace links) when helpful
- Use Conventional Commits or clear imperative titles; link issues/tasks

## Exceptions

Exceptions to these rules must be justified in the PR description with rationale and trade-offs. Consider an ADR for significant deviations.

---

See stack specifics:

- `./backend-python.md`
- `./frontend-typescript.md`
