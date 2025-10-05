# Calorie Intake Logger (Polish) — PoC Project Description

**Version:** v0.1
**Date:** 2025-10-05
**Owner:** Michał

---

## 1) Summary

A web app Proof‑of‑Concept that estimates daily calorie and macro intake from **free‑text Polish descriptions** of what the user ate. The system uses a **hosted LLM** to parse text into **raw ingredients** and quantities, then performs **RAG retrieval** over a food database in Supabase Postgres (`pgvector`) to ground calculations in per‑100g nutrition facts. Users authenticate via **Supabase Auth**, can **edit/delete** logged meals, and view daily totals. The PoC targets **accuracy evaluation** on ~100 labeled meals.

---

## 2) Goals & Non‑Goals

**Goals**

- Fast, accurate extraction of foods and quantities from Polish free text.
- Compute calories & macros (protein, fat, carbs) using **raw product decomposition**.
- Hybrid retrieval (full‑text + vector) in **Postgres (`pgvector`)** with Polish text config & synonyms.
- Minimal, clear UX for logging, clarifications, editing, and daily summaries.
- Evaluate accuracy (MAE) vs. labeled set of ~100 meals.

**Non‑Goals (PoC)**

- Full coverage of branded databases; only a seed catalog + optional Open Food Facts subset.
- Cooking transformations (raw→cooked adjustments) beyond basic density conversions.
- Image/voice input; **text‑only** in v1.
- GDPR features beyond basics; no EU‑residency guarantees.
- Advanced diet coaching; focus is logging and totals.

---

## 3) Primary User Stories

1. As a user, I can sign in and store a profile (age/sex/height/weight/activity/goal).
2. I can write

   > "Śniadanie: owsianka na mleku 2%, banan, garść orzechów."
   > and get a parsed list of **raw ingredients** with estimated grams.

3. If something is ambiguous, I get **one short clarifying question** in Polish.
4. I can save the meal, see per‑item and total kcal/macros, and **edit or delete** later.
5. I can open a **day view** to see totals for that date.

---

## 4) Product Scope (MVP)

- **Auth:** Supabase Auth (hosted).
- **Input:** Polish free text only.
- **LLM:** Hosted, low‑cost instruction model (good Polish support).
- **RAG:** Postgres (`pgvector`) hybrid retrieval; optional citations to source entries.
- **Data:** Curated CSV of common foods (PL) + optional Open Food Facts subset.
- **Quantities:** Household measures → grams with confidence; ml→g via densities.
- **Meals:** Create, list, edit, delete; daily totals.
- **Evaluation:** MAE for kcal/macros on ~100 meals + retrieval top‑1 accuracy.

---

## 5) High‑Level Architecture

- **Frontend:** Next.js + TypeScript, Tailwind, shadcn/ui

  - Pages: `/login`, `/log`, `/day/:date`, `/history`
  - Chat‑like input, inline clarifications, inline item editing

- **Backend:** FastAPI (Python)

  - LLM orchestration & prompting (parse + clarify)
  - Quantity normalization (household measures → grams)
  - Retriever (Postgres full‑text + `pgvector` ANN), rerank, thresholds
  - Calculator (scale per‑100g macros by grams)
  - Persistence via Supabase Postgres

- **Stores:**

- **Supabase Postgres** (hosted, with `pgvector`) for food catalog (vectors + full‑text), users, profiles, meals

- **Infra:** Local Docker Compose for frontend and API (Supabase hosted with `pgvector`)

---

## 6) Core Flow (per meal)

1. **Parse:** LLM converts Polish text → JSON items (labels, estimated grams/ml, confidences).
2. **Normalize:** Convert household measures to grams; ml→g using density where available.
3. **Retrieve:** Query Postgres using hybrid (full‑text + vector via `pgvector`) with Polish config & synonyms.
4. **Disambiguate:** If score < τ or low confidence → ask a **single clarifying question**.
5. **Calculate:** Scale per‑100g macros to grams; aggregate totals.
6. **Persist & Display:** Save meal/items; show totals; allow edit/delete.

---

## 7) Data Sources & Ingestion (PoC)

- **Seed CSV (2–5k entries)** of common Polish raw foods with per‑100g macros, densities (where applicable), and synonyms.
- **Open Food Facts (PL locale)** subset for popular branded items (optional).
- Keep `source` and `source_ref` for traceability.
- Simple ETL script to compute embeddings and upsert into Postgres (`pgvector`).

> Scraping full IŻŻ/USDA can follow later if needed; PoC prioritizes coverage for common foods.

---

## 8) Data Model

### 8.1 Postgres Tables: `foods`

- `id: uuid`
- `name_pl: text` (Polish full‑text search config; optional trigram index for autocomplete)
- `name_en: text` (optional)
- `brand: text` (nullable)
- `category: text`
- `macros_per_100g: jsonb { kcal, protein_g, fat_g, carbs_g }`
- `density_g_per_ml: real` (nullable)
- `unit_synonyms: text` (e.g., "łyżka, łyżeczka, szklanka, plaster, kromka, garść")
- `source: text` (e.g., `IZZZ`, `USDA`, `OFF`, `manual`)
- `source_ref: text`
- `embedding: vector(dim = <embedding_dim>)` (via `pgvector`)
- `name_pl_tsv: tsvector` (generated from `name_pl` with Polish config)

**Retrieval**: Hybrid full‑text (`tsvector`/`tsquery`) + vector similarity with weighted fusion; synonyms via table and query‑time expansion (e.g., "twaróg = ser biały").

### 8.2 Supabase Postgres (Core)

- `profiles(user_id, sex, birth_date, height_cm, weight_kg, activity_level, goal)`
- `meals(id, user_id, eaten_at, note, total_kcal, total_protein_g, total_fat_g, total_carbs_g)`
- `meal_items(id, meal_id, food_id, label, grams, kcal, protein_g, fat_g, carbs_g, source_ref, match_score, parse_confidence)`
- `edits(id, meal_id, user_id, changed_at, before_json, after_json)`

---

## 9) API Contracts (FastAPI, JSON)

### POST `/parse`

**Req** `{ text: string }`
**Res** `{ items: [{ label, quantity_expr?, grams?, ml?, confidence }], needs_clarification: boolean }`

### POST `/match`

**Req** `{ items: [{ label: string, grams: number }] }`
**Res** `{ matches: [{ label, food_id, source, source_ref?, match_score, macros_per_100g }] }`

### POST `/log`

**Req** `{ eaten_at?: ISODate, note?: string, items: [{ food_id, label, grams }] }`
**Res** `{ meal_id, totals: { kcal, protein_g, fat_g, carbs_g }, items: [...] }`

### GET `/summary?date=YYYY-MM-DD`

**Res** `{ date, totals: {...}, meals: [{ id, eaten_at, items: [...], totals: {...} }] }`

### GET `/foods/search?q=`

Autocomplete for manual corrections / additions.

---

## 10) LLM & Prompting

- **Model:** hosted, low‑cost instruction model with good Polish comprehension.
- **Temperature:** ~0.2 for deterministic parsing.
- **Parsing prompt (PL, JSON‑only):**

  - Extract **raw ingredients**, infer grams/ml from household phrases; include `confidence` and `quantity_expr` when approximated.
  - Do not invent brands; prefer generic labels.
  - If uncertain, still output best estimate with lower confidence.

- **Clarification prompt (PL):**

  - Produce **one short question** with up to 3 options (or numeric ask) targeting the highest‑impact ambiguity.

**Thresholds**

- `parse_confidence` and retrieval `match_score` used to decide **A/B policy**:

  - **A (auto‑approx):** high confidence and score ≥ τ.
  - **B (ask):** below threshold or inherently ambiguous foods (e.g., pizza styles/sizes).

---

## 11) Quantity Normalization

- **Household measures table** (e.g., łyżka, łyżeczka, szklanka, plaster, kromka, garść) with per‑food defaults or ranges.
- **Densities** for common liquids (e.g., mleko 2% ≈ 1.03 g/ml).
- If unknown density, fallback category averages; record `parse_confidence`.

---

## 12) Calculations

Per item:
`kcal_item = macros_per_100g.kcal * grams / 100` (likewise protein/fat/carbs).
Per meal/day: sums of items.

Optional **citations**: store `source` & `source_ref` used for each item.

---

## 13) Frontend UX

- **/log:** single text box → preview parsed items → inline clarify (when needed) → confirm & save.
- **Inline edits:** change grams or swap matched food via search.
- **/day/:date:** list meals + per‑day totals; delete/edit meal.
- **/history:** simple date picker.

---

## 14) Evaluation Plan (100 meals)

- **Dataset:** Polish sentences with gold standard (items, grams, totals).
- **Metrics:**

  - **MAE** of kcal per meal; **MAE** for macros.
  - **Top‑1 retrieval accuracy** (matched food = gold).
  - **Clarification rate** (% meals needing a question).

- **Targets (example):** kcal MAE ≤ 80 kcal/meal; Top‑1 ≥ 85%; Clarifications ≤ 25%.

---

## 15) DevOps & Deployment

- **Local:** Docker Compose

  - Services: `frontend` (Next.js), `api` (FastAPI).
  - Supabase remains **hosted** with `pgvector`; env keys injected to frontend & API.

- **Monitoring (PoC):** basic request logs + error tracing.

---

## 16) Security & Privacy

- **Auth:** Supabase Auth; email/password or provider per Supabase config.
- **PII:** minimal (profile + login).
- **Secrets:** stored via `.env` in Docker, never committed.
- **Data deletion:** edit/delete meals supported; full account deletion out of scope for PoC.

---

## 17) Risks & Mitigations

- **Polish ambiguity / slang:** maintain synonyms file; prompt tuning; clarifications.
- **Catalog gaps:** allow manual selection; flag missing foods for later curation.
- **Unit ambiguity:** household table with ranges; conservative defaults; ask user when high impact.
- **LLM cost/latency:** cache parsed results by input hash; small model; batch embeddings.
- **Evaluation bias:** ensure dataset covers mixed dishes and fuzzy quantities.

---

## 18) Roadmap (2 Weeks)

**Week 1**

1. Repo, Docker, Supabase Auth + profiles.
2. Supabase Postgres `pgvector` ready, seed CSV, embeddings.
3. FastAPI `/parse`, `/match`, `/log` (happy path).
4. Next.js UI: login, meal entry, day summary.

**Week 2** 5) Clarification UX + thresholds. 6) Edit/delete with recount. 7) Evaluator script + labeled set run. 8) Polish synonyms & household table polish; demo script.

---

## 19) Open Questions (tracked)

- Add minimal **citations** UI toggle? (off by default)
- Include **OFF branded** subset in PoC seed?
- Store **BMR/targets** and show daily progress rings? (spec allows; optional UI)
- Which exact hosted LLM & embeddings API (final pick during implementation)?

---

## 20) Appendix

### A) Example Parse Output (LLM)

```json
{
  "items": [
    {
      "label": "płatki owsiane",
      "quantity_expr": "60 g",
      "grams": 60,
      "confidence": 0.92
    },
    {
      "label": "mleko 2%",
      "quantity_expr": "200 ml",
      "ml": 200,
      "grams": 206,
      "confidence": 0.86
    },
    {
      "label": "banan",
      "quantity_expr": "1 sztuka (średni)",
      "grams": 118,
      "confidence": 0.78
    },
    {
      "label": "orzechy włoskie",
      "quantity_expr": "garść",
      "grams": 30,
      "confidence": 0.65
    }
  ],
  "needs_clarification": false
}
```

### B) Example Clarification (LLM output)

> "O jakie mleko chodziło?"
> **1)** krowie 2% **2)** napój migdałowy **3)** inne (podaj)

### C) Household Measures (excerpt)

- łyżeczka cukru ≈ 4–5 g
- łyżka oliwy ≈ 10–12 g
- szklanka mleka ≈ 240–250 ml (≈ 247–258 g dla 2%)
- garść orzechów włoskich ≈ 25–35 g (domyślnie 30 g)

---

## 21) Architecture Diagram (ASCII)

### 21.1 Component / Dependency View

```
                                           (Hosted)
                                    +-------------------+
                                    |   Supabase Auth   |
                                    |  (JWT issuance)   |
                                    +---------+---------+
                                              ^
                                              | OIDC/JWT (sign-in)
+-----------------------+   HTTPS    +--------+---------+         (Hosted)
|       Browser         +----------->|   Next.js UI     |<----+  +--------------------+
|  (User device)        |            | TypeScript/Tailw |     |  | Supabase Postgres  |
+-----------+-----------+            | shadcn/ui        |     |  |  (users, profiles, |
            |                         +--------+--------+     |  |   meals, items)    |
            | HTTPS (JWT)                      |               |  +---------+----------+
            v                                   \              |            ^
+-----------+-----------+                        \             |            | SQL/REST
|         FastAPI       |                         \            |            |
|  Orchestrator/Pipeline|                          v           |            |
|  /parse /match /log   |                  +-------+-------+    |            |
|  Quantity Normalizer  |                  |  BFF API routes |---+------------
+---+----+----+----+----+                  |  (Next.js)      |    writes/reads
    |    |    |    |                       +-------+---------+
    |    |    |    |                               |
    |    |    |    |                               | HTTP (internal)
    |    |    |    |                               v
    |    |    |    |                       +-------+-------+
    |    |    |    +---------------------->|  FastAPI      |  (same as above)
    |    |    |                            +-------+-------+
    |    |    |                                    |
    |    |    |                                    | Retrieval (hybrid)
    |    |    |                                    v
    |    |    |                         +-------------------------------+
    |    |    +------------------------>|  Supabase Postgres (pgvector) |
    |    |                              |  FTS + vector (RAG)           |
    |    |                              +-------------------------------+
    |    |
    |    |  Parse / Clarify (cheap hosted model)
    |    +------------------------------------------+
    |                                               v
    |                                      +--------+---------+   (Hosted)
    |                                      |    LLM API       |
    |                                      |  (Polish parsing |
    |                                      |   & questions)   |
    |                                      +------------------+
    |
    |  Persist meals/items, totals
    +---------------------------------------------------------->
                                                             (Hosted)
                                                        +----+---------+
                                                        | Supabase     |
                                                        | Postgres     |
                                                        +--------------+

             Ingestion / Offline
             --------------------
(Seed CSV + OFF subset)                 (Hosted)
+----------------------+        +------------------------+
|  Food Catalog CSV    | -----> |  Embeddings API       |
|  (PL raw foods)      |        |  (vectorize entries)  |
+----------+-----------+        +----------+-------------+
           | ETL script (Docker)            |
           v                                v
      +----+---------------------------------+----+
      |     Supabase Postgres (foods table)      |
      |  FTS + pgvector (embedding column)       |
      +------------------------------------------+

Evaluation / Tooling
--------------------
+--------------------+        run tests        +----------------------+
|  Evaluator Script  +-----------------------> |  FastAPI endpoints   |
| (100 labeled meals)|                         | (/parse,/match,/log) |
+--------------------+                         +----------------------+
```

### 21.2 Request Flow (Happy Path)

```
User        Next.js UI       FastAPI         LLM API         Postgres(FTS+vec)  Supabase DB
 |             |               |               |                |               |
 |  text input |               |               |                |               |
 |-----------> |               |               |                |               |
 |             |  POST /api/parse (JWT)        |                |               |
 |             |--------------> |               |                |               |
 |             |               |  call parse -> |                |               |
 |             |               |--------------> |                |               |
 |             |               |   JSON items   |                |               |
 |             |               |<-------------- |                |               |
 |             |               | normalize qty  |                |               |
 |             |               |  retrieve ---->|  FTS + vector  |               |
 |             |               |--------------> |---------------> |               |
 |             |               |   matches      |                |               |
 |             |               |<-------------- |<--------------- |               |
 |             |  show preview + totals         |                |               |
 |             |<-------------- |               |                |               |
 | confirm     |               |               |                |               |
 |-----------> |  POST /api/log (items, grams)  |                |               |
 |             |--------------> | persist items -------------------------------> |
 |             |               |----------------------------------------------> |
 |             |               |  respond totals |                |               |
 |             |<-------------- |               |                |               |
 |  day view   |  GET /api/summary?date=YYYY-MM-DD              |               |
 |-----------> |--------------> |                                |               |
 |             |<-------------- |  meals + totals                |               |
```

### 21.3 Clarification Branch (When Ambiguous)

```
... parse -> low confidence or low match score ...
FastAPI -> LLM: generate ONE short PL question (<=3 options)
Next.js shows inline question -> user selects/edits -> repeat match -> compute totals
```
