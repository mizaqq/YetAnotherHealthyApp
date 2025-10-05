# Task 02 — LLM Orchestration Hardening

## Objective

Make `parse_text()` and `clarify_question()` deterministic, observable, and safe using structured outputs, timeouts/retries, and golden tests.

## Outcomes

- Stable JSON‑schema outputs; temperature ~0.
- Prompt versioning and replay tool.
- Cost and latency logged per request.

## Deliverables

- `api/app/services/llm.py` with interface and provider client.
- `prompts/parse_v1.md`, `prompts/clarify_v1.md` (versioned).
- Golden tests under `api/tests/llm_golden/` with fixtures and expected JSON.

## Steps

1. Define JSON Schema for outputs

- `parse_text()`: items with labels, grams/ml, confidences, quantity_expr, needs_clarification.
- `clarify_question()`: one question, up to 3 options or numeric ask.

2. Implement client wrapper

- Retries with exponential backoff; max attempts and jitter.
- Timeouts; HTTP failures surface meaningful errors.
- Token budget/response size guardrails.

3. Determinism

- Temperature ~0; model parameters fixed; seed where provider supports.

4. Prompt versioning and replay

- Store prompts in `prompts/` with explicit versions.
- Replay tool to run a corpus and diff JSON outputs.

5. Golden tests

- Create fixed inputs → check exact JSON match.
- Run in CI; failing diffs are actionable.

## Acceptance Criteria

- Golden tests pass reliably across runs/PRs.
- Logs include per‑call duration and (if available) cost.
- Replay tool can compare v1 vs v2 outputs.

## Risks & Mitigations

- Provider instability: retries/backoff and golden gating; allow provider swap via interface.
- JSON drift: strict schema validation and defensive parsing.

## Estimated Time

- 0.5–1 day

