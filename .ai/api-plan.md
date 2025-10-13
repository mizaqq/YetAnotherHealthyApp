# REST API Plan

## 1. Resources

- `Session` → Supabase `auth.users` (identity, handled by Supabase Auth)
- `Profile` → `public.profiles`
- `MealCategory` → `public.meal_categories`
- `UnitDefinition` → `public.unit_definitions`
- `UnitAlias` → `public.unit_aliases`
- `Product` → `public.products`
- `ProductPortion` → `public.product_portions`
- `Meal` → `public.meals`
- `AnalysisRun` → `public.analysis_runs`
- `AnalysisRunItem` → `public.analysis_run_items`
- `Report` (aggregated) → derived from `public.meals`, `public.analysis_runs`

## 2. Endpoints

### 2.2 Profile

- **GET** `/api/v1/profile`
  - **Description:** Return current user profile with onboarding state.
  - **Response JSON:**

```json
{
  "user_id": "uuid",
  "daily_calorie_goal": 2000.0,
  "onboarding_completed_at": "2025-10-10T08:15:00Z",
  "created_at": "2025-10-01T07:00:00Z",
  "updated_at": "2025-10-10T08:15:00Z"
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found` (profile missing), `401 Unauthorized`

- **POST** `/api/v1/profile/onboarding`
  - **Description:** Create or complete onboarding with calorie goal; idempotent.
  - **Request JSON:**

```json
{
  "daily_calorie_goal": 2000.0
}
```

- **Response JSON:** `GET /api/v1/profile` payload
- **Success:** `201 Created`
- **Errors:** `400 Bad Request` (invalid goal), `409 Conflict` (profile already completed), `401 Unauthorized`

- **PATCH** `/api/v1/profile`
  - **Description:** Update calorie goal, mark onboarding completion.
  - **Request JSON:**

```json
{
  "daily_calorie_goal": 2200.0,
  "onboarding_completed_at": "nullable ISO timestamp"
}
```

- **Response JSON:** updated profile payload
- **Success:** `200 OK`
- **Errors:** `400 Bad Request`, `401 Unauthorized`

### 2.3 Meal Categories

- **GET** `/api/v1/meal-categories`
  - **Description:** List canonical meal categories sorted by `sort_order`.
  - **Query Params:** `locale` (default `pl-PL` for labels), optional `include_inactive` (future-proof).
  - **Response JSON:**

```json
{
  "data": [
    { "code": "breakfast", "label": "Śniadanie", "sort_order": 1 },
    { "code": "lunch", "label": "Obiad", "sort_order": 3 }
  ]
}
```

- **Success:** `200 OK`
- **Errors:** `401 Unauthorized`

### 2.4 Units

- **GET** `/api/v1/units`
  - **Description:** List unit definitions with gram equivalents.
  - **Query Params:** `unit_type`, `search`, `page[size]` (≤100), `page[after]` (cursor).
  - **Response JSON:**

```json
{
  "data": [
    {
      "id": "uuid",
      "code": "g",
      "unit_type": "mass",
      "grams_per_unit": "1.0000"
    }
  ],
  "page": { "size": 50, "after": "opaque-cursor" }
}
```

- **Success:** `200 OK`
- **Errors:** `401 Unauthorized`

- **GET** `/api/v1/units/{unit_id}/aliases`
  - **Description:** Return localized aliases for a unit.
  - **Query Params:** `locale` (default `pl-PL`).
  - **Response JSON:**

```json
{
  "unit_id": "uuid",
  "aliases": [{ "alias": "łyżka", "locale": "pl-PL", "is_primary": true }]
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found`, `401 Unauthorized`

### 2.5 Products

- **GET** `/api/v1/products`
  - **Description:** Search canonical products for AI suggestions and manual selection.
  - **Query Params:** `search`, `off_id`, `source`, `page[size]` (≤50), `page[after]` (cursor), `include_macros` (bool).
  - **Response JSON:**

```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Greek Yogurt",
      "macros_per_100g": {
        "calories": 59.0,
        "protein": 10.0,
        "fat": 0.0,
        "carbs": 3.6
      },
      "source": "open_food_facts"
    }
  ],
  "page": { "size": 20, "after": "opaque-cursor" }
}
```

- **Success:** `200 OK`
- **Errors:** `400 Bad Request` (invalid filter), `401 Unauthorized`

- **GET** `/api/v1/products/{product_id}`
  - **Description:** Retrieve detailed product info, optionally including portions.
  - **Query Params:** `include_portions` (bool).
  - **Response JSON:**

```json
{
  "id": "uuid",
  "name": "Greek Yogurt",
  "off_id": "123456",
  "macros_per_100g": {
    "calories": 59.0,
    "protein": 10.0,
    "fat": 0.0,
    "carbs": 3.6
  },
  "source": "open_food_facts",
  "created_at": "2025-09-01T10:00:00Z",
  "updated_at": "2025-09-05T08:00:00Z",
  "portions": [
    {
      "id": "uuid",
      "unit_definition_id": "uuid",
      "grams_per_portion": 125.0,
      "is_default": true,
      "source": "producer"
    }
  ]
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found`, `401 Unauthorized`

- **GET** `/api/v1/products/{product_id}/portions`
  - **Description:** Retrieve all portions tied to a product.
  - **Response JSON:** array of portion objects as above.
  - **Success:** `200 OK`
  - **Errors:** `404 Not Found`, `401 Unauthorized`

### 2.6 Meals

- **POST** `/api/v1/meals`
  - **Description:** Persist a meal entry. Supports AI (`source=ai`), edited (`source=edited`), or manual (`source=manual`).
  - **Request JSON:**

```json
{
  "category": "breakfast",
  "eaten_at": "2025-10-12T07:30:00Z",
  "source": "ai",
  "calories": 450.0,
  "protein": 25.0,
  "fat": 15.0,
  "carbs": 55.0,
  "analysis_run_id": "uuid",
  "notes": "AI generated"
}
```

- **Rules:**
  - `source=ai|edited` requires `analysis_run_id` referencing succeeded run for same user and macros present.
  - `source=manual` forbids `analysis_run_id` and macros other than calories.
- **Response JSON:**

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "category": "breakfast",
  "eaten_at": "2025-10-12T07:30:00Z",
  "source": "ai",
  "calories": 450.0,
  "protein": 25.0,
  "fat": 15.0,
  "carbs": 55.0,
  "accepted_analysis_run_id": "uuid",
  "created_at": "2025-10-12T07:31:00Z",
  "updated_at": "2025-10-12T07:31:00Z"
}
```

- **Success:** `201 Created`
- **Errors:** `400 Bad Request`, `401 Unauthorized`, `404 Not Found` (analysis run/category), `409 Conflict` (duplicate acceptance)

- **GET** `/api/v1/meals`
  - **Description:** List meals with filters for history views.
  - **Query Params:** `from` (date), `to` (date), `category`, `source`, `include_deleted` (bool, default false), `page[size]` (≤100), `page[after]` (cursor), `sort` (default `-eaten_at`).
  - **Response JSON:**

```json
{
  "data": [
    {
      "id": "uuid",
      "category": "breakfast",
      "eaten_at": "2025-10-12T07:30:00Z",
      "calories": 450.0,
      "protein": 25.0,
      "fat": 15.0,
      "carbs": 55.0,
      "source": "ai",
      "accepted_analysis_run_id": "uuid"
    }
  ],
  "page": { "size": 20, "after": "opaque-cursor" }
}
```

- **Success:** `200 OK`
- **Errors:** `401 Unauthorized`, `400 Bad Request`

- **GET** `/api/v1/meals/{meal_id}`
  - **Description:** Detailed meal view including accepted analysis run snapshot.
  - **Query Params:** `include_analysis_items` (bool to embed ingredients).
  - **Response JSON:**

```json
{
  "id": "uuid",
  "category": "breakfast",
  "eaten_at": "2025-10-12T07:30:00Z",
  "source": "ai",
  "calories": 450.0,
  "protein": 25.0,
  "fat": 15.0,
  "carbs": 55.0,
  "analysis": {
    "run": { "id": "uuid", "status": "succeeded", "run_no": 1 },
    "items": [
      {
        "id": "uuid",
        "ordinal": 1,
        "raw_name": "owsianka",
        "weight_grams": 100.0,
        "calories": 350.0,
        "confidence": 0.92
      }
    ]
  }
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found`, `401 Unauthorized`

- **PATCH** `/api/v1/meals/{meal_id}`
  - **Description:** Update meal metadata or convert manual entry to edited (requires new analysis run).
  - **Request JSON:**

```json
{
  "category": "lunch",
  "eaten_at": "2025-10-12T12:00:00Z",
  "calories": 480.0,
  "protein": 30.0,
  "fat": 18.0,
  "carbs": 52.0,
  "source": "edited",
  "analysis_run_id": "uuid"
}
```

- **Success:** `200 OK`
- **Errors:** `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `409 Conflict`

- **DELETE** `/api/v1/meals/{meal_id}`
  - **Description:** Soft-delete meal (set `deleted_at`).
  - **Success:** `204 No Content`
  - **Errors:** `404 Not Found`, `401 Unauthorized`

### 2.7 Analysis Runs

- **POST** `/api/v1/analysis-runs`
  - **Description:** Trigger AI analysis pipeline for a meal draft or manual description.
  - **Request JSON:**

```json
{
  "meal_id": "nullable uuid",
  "input_text": "Owsianka z bananem i miodem",
  "threshold": 0.8
}
```

- **Behavior:**
  - If `meal_id` omitted, create draft run tied to user; results accepted via `POST /api/v1/meals`.
  - Returns 202 when queued; synchronous response includes run metadata.
- **Response JSON:**

```json
{
  "id": "uuid",
  "meal_id": null,
  "run_no": 1,
  "status": "queued",
  "threshold_used": 0.8,
  "created_at": "2025-10-12T07:29:30Z"
}
```

- **Success:** `202 Accepted`
- **Errors:** `400 Bad Request`, `401 Unauthorized`, `409 Conflict` (concurrent run exists)

- **GET** `/api/v1/analysis-runs`

  - **Description:** Paginated list of runs for observability.
  - **Query Params:** `meal_id`, `status`, `created_from`, `created_to`, `page[size]` (≤50), `page[after]` (cursor), `sort` (default `-created_at`).
  - **Response JSON:**

```json
{
  "data": [
    {
      "id": "uuid",
      "meal_id": "uuid",
      "run_no": 1,
      "status": "succeeded",
      "threshold_used": 0.8,
      "created_at": "2025-10-12T07:29:30Z",
      "completed_at": "2025-10-12T07:29:39Z"
    }
  ],
  "page": { "size": 20, "after": "opaque-cursor" }
}
```

- **Success:** `200 OK`
- **Errors:** `401 Unauthorized`

- **GET** `/api/v1/analysis-runs/{run_id}`
  - **Description:** Run detail including metrics and error payload.
  - **Response JSON:**

```json
{
  "id": "uuid",
  "meal_id": "uuid",
  "run_no": 2,
  "status": "failed",
  "latency_ms": 10500,
  "tokens": 2200,
  "cost_minor_units": 32,
  "cost_currency": "USD",
  "threshold_used": 0.8,
  "retry_of_run_id": "uuid",
  "error_code": "TIMEOUT",
  "error_message": "Model response exceeded limit",
  "created_at": "2025-10-12T07:40:00Z",
  "completed_at": "2025-10-12T07:40:11Z"
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found`, `401 Unauthorized`

- **GET** `/api/v1/analysis-runs/{run_id}/items`

  - **Description:** Ingredient-level breakdown for a run.
  - **Response JSON:**

```json
{
  "run_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "ordinal": 1,
      "raw_name": "płatki owsiane",
      "raw_unit": "łyżka",
      "quantity": 3.5,
      "unit_definition_id": "uuid",
      "product_id": "uuid",
      "product_portion_id": null,
      "weight_grams": 105.0,
      "confidence": 0.92,
      "calories": 380.0,
      "protein": 13.0,
      "fat": 7.0,
      "carbs": 65.0
    }
  ]
}
```

- **Success:** `200 OK`
- **Errors:** `404 Not Found`, `401 Unauthorized`

- **POST** `/api/v1/analysis-runs/{run_id}/retry`
  - **Description:** Schedule retry using stored `raw_input`; increments `run_no` for meal.
  - **Request JSON:**

```json
{
  "threshold": 0.75,
  "raw_input": {
    "text": "Owsianka z jabłkiem",
    "overrides": {
      "excluded_ingredients": ["orzechy"],
      "notes": "User removed nuts"
    }
  }
}
```

- **Response JSON:** new run metadata (`202 Accepted`).
- **Errors:** `409 Conflict` (run still in progress), `404 Not Found`, `401 Unauthorized`

- **POST** `/api/v1/analysis-runs/{run_id}/cancel`
  - **Description:** Mark an in-flight run as `cancelled` (best-effort cancellation).
  - **Success:** `202 Accepted`
  - **Errors:** `409 Conflict` (already terminal), `404 Not Found`, `401 Unauthorized`

### 2.8 Reports

- **GET** `/api/v1/reports/daily-summary`
  - **Description:** Aggregate totals for selected date.
  - **Query Params:** `date` (ISO date, default today).
  - **Response JSON:**

```json
{
  "date": "2025-10-12",
  "calorie_goal": 2000.0,
  "totals": {
    "calories": 1650.0,
    "protein": 95.0,
    "fat": 55.0,
    "carbs": 180.0
  },
  "progress": {
    "calories_percentage": 82.5
  },
  "meals": [
    {
      "id": "uuid",
      "category": "breakfast",
      "calories": 450.0,
      "eaten_at": "2025-10-12T07:30:00Z"
    }
  ]
}
```

- **Success:** `200 OK`
- **Errors:** `400 Bad Request`, `401 Unauthorized`

- **GET** `/api/v1/reports/weekly-trend`
  - **Description:** Seven-day rolling trend aggregated by date, including zero-intake days.
  - **Query Params:** `end_date` (default today), `include_macros` (bool).
  - **Response JSON:**

```json
{
  "start_date": "2025-10-06",
  "end_date": "2025-10-12",
  "points": [
    { "date": "2025-10-06", "calories": 1900.0, "goal": 2000.0 },
    { "date": "2025-10-07", "calories": 0.0, "goal": 2000.0 }
  ]
}
```

- **Success:** `200 OK`
- **Errors:** `400 Bad Request`, `401 Unauthorized`

## 3. Authentication and Authorization

- Supabase JWT in `Authorization: Bearer <token>` header; FastAPI dependency verifies token via Supabase REST API or JWT secret, extracts `auth.uid()` for RLS alignment.
- Every query filters by `user_id = auth.uid()` to satisfy RLS policies on `profiles`, `meals`, `analysis_runs`, `analysis_run_items`.
- Service-role endpoints (dictionary maintenance) are excluded from public API; dictionaries are read-only for authenticated users to match RLS guidance.
- Sessions expire per Supabase configuration; backend returns `401` when token invalid/expired.
- Apply rate limiting (e.g., 60 req/min per IP + user for write endpoints, 120 req/min for read) via FastAPI middleware or API gateway.

## 4. Validation and Business Logic

- **Profiles:** ensure `daily_calorie_goal ≥ 0`; `onboarding_completed_at` can only be set once and must be ≥ `created_at`.
- **Meals:** category must exist; `eaten_at` required; macros/cals must be non-negative decimals; `source=manual` requires `calories` only and null macros; `source in {ai, edited}` requires macros and `analysis_run_id` referencing succeeded run; enforce single acceptance per run (`409 Conflict` if already used); soft-delete sets `deleted_at` but retains data for reports using `include_deleted=false` by default.
- **Analysis Runs:** `run_no` auto-increment per meal; status transitions limited to `queued→running→succeeded|failed|cancelled`; `latency_ms`, `tokens`, `cost_minor_units` validated as non-negative; retries require previous run in `failed|succeeded` states; `threshold` bounded 0-1.
