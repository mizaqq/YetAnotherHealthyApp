# Task 04 — Early Evaluation (Dev Dataset + Evaluator)

## Objective

Introduce a small labeled dataset and an evaluator that computes MAE and retrieval accuracy; run it in CI early.

## Outcomes

- `evaluation/dataset.dev.jsonl` (20 meals) with gold labels.
- Evaluator script producing JSON/CSV reports under `evaluation/reports/`.

## Deliverables

- `evaluation/dataset.dev.jsonl` schema: `{ text, items:[{label, grams}], totals:{kcal,protein_g,fat_g,carbs_g} }`.
- `evaluation/run_eval.py` (calls services directly or HTTP endpoints).
- Make target: `make eval-ci` to run evaluator in CI and store artifacts.

## Steps

1. Create dataset

- Curate 20 Polish meal descriptions covering common foods and ambiguous units.
- Provide gold items with grams and totals.

2. Implement evaluator

- For each sample: run parse → normalize → match → calculate (or use API endpoints if available).
- Metrics: MAE per meal (kcal/macros), top‑1 retrieval accuracy, clarification rate.
- Save consolidated report JSON and a CSV summary.

3. Integrate with CI

- Upload artifacts from `evaluation/reports/*` on PRs.
- Initially warn-only; plan to gate once baseline stabilizes.

## Acceptance Criteria

- `make eval-ci` runs locally and in CI; artifacts produced.
- Report includes all three metrics and per‑sample breakdown.

## Risks & Mitigations

- Unstable results: fix prompts and seeds; cache parse outputs by input hash.

## Estimated Time

- 0.5 day

