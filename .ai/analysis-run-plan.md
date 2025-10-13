# API Endpoint Implementation Plan: POST /api/v1/analysis-runs

## 1. Przegląd punktu końcowego

- Kolejkuje nowy przebieg analizy AI dla posiłku lub wolnego opisu, zapisując stan w Supabase.
- Tworzy rekord `analysis_runs` i inicjuje asynchroniczny pipeline budujący `analysis_run_items`.
- Zapewnia idempotencję i kontrolę równoległych analiz poprzez walidację statusów istniejących przebiegów.

## 2. Szczegóły żądania

- Metoda HTTP: POST
- Struktura URL: /api/v1/analysis-runs
- Wymagane nagłówki: Authorization Bearer <Supabase JWT>, Content-Type application/json
- Parametry wymagane: `input_text` (gdy brak `meal_id`), obecny token JWT.
- Parametry opcjonalne: `meal_id` (UUID, posiłek użytkownika, nieusunięty), `threshold` (0.0–1.0, domyślnie 0.8).
- Request Body:
  - `meal_id`: uuid | null
  - `input_text`: string | null (1–2000 znaków po trim)
  - `threshold`: number | null (Decimal(3,2))

```json
{
  "meal_id": "uuid|null",
  "input_text": "Owsianka z bananem i miodem",
  "threshold": 0.8
}
```

## 3. Wykorzystywane typy

- `AnalysisRunCreatePayload` (Pydantic) z walidatorami `constr`, `UUID4`, `condecimal`.
- `AnalysisRunQueuedResponse` (Pydantic) odwzorowujący pola Supabase `analysis_runs.Row`.
- `CreateAnalysisRunCommand` (dataclass) przechowujący `user_id`, `meal`, `raw_input`, `threshold`.
- `AnalysisRunRepository` korzystające z supabase’owych `TablesInsert<"analysis_runs">` i `Tables<"analysis_runs">` oraz metod `get_active_run`, `get_meal`, `insert_run`.
- Background DTO `AnalysisPipelinePayload` dla kolejki (run_id, raw_input, threshold, model).

## 4. Szczegóły odpowiedzi

- Status sukcesu: 202 Accepted.
- Body:

```json
{
  "id": "9f6e6b3e-2f9a-4f3b-a0d5-3cc8f0349d1a",
  "meal_id": null,
  "run_no": 1,
  "status": "queued",
  "threshold_used": 0.8,
  "model": "openrouter/gpt-4o-mini",
  "created_at": "2025-10-12T07:29:30Z",
  "retry_of_run_id": null,
  "latency_ms": null
}
```

- Nagłówki: `Location: /api/v1/analysis-runs/{id}`, `Retry-After: 5`.
- Błędy: 400, 401, 404, 409, 500 z opisami w sekcji Obsługa błędów.

## 5. Przepływ danych

- FastAPI dependency sprawdza JWT Supabase i zwraca `user_id`.
- Handler waliduje payload, buduje `CreateAnalysisRunCommand`.
- Serwis `AnalysisRunService.create_run`:
  - Pobiera posiłek (`analysis_runs.meal_id`), weryfikuje własność i `deleted_at`.
  - Sprawdza brak aktywnego przebiegu (status queued/running) dla `meal_id`.
  - Oblicza `run_no` (1 + max istniejący).
  - Wstawia rekord `analysis_runs` (status queued, `threshold_used`, `raw_input`).
  - Dodaje zadanie do `BackgroundTasks` lub zewnętrznej kolejki.
- Worker AI aktualizuje rekord (`status`, `raw_output`, `latency_ms`) oraz zapisuje `analysis_run_items`.

## 6. Względy bezpieczeństwa

- Supabase JWT + RLS: wszystkie inserty/selekt w kontekście `user_id`.
- Walidacja własności `meal_id` (repo używa zapytań filtrowanych po `user_id`).
- Sanitizacja `input_text`: `strip`, usunięcie znaków kontrolnych, limit długości, normalizacja białych znaków.
- Rate limiting (opcjonalny dependency) zapobiega nadużyciom.
- Audit logging: `trace_id`, `user_id`, `meal_id`, `request_id`.
- Chronić przed prompt injection przez przechowywanie surowego wejścia w `raw_input` objętym zasadami RLS.

## 7. Obsługa błędów

- 400 Bad Request:
  - Brak `meal_id` i `input_text`.
  - `threshold` poza 0–1.
  - `input_text` po trim ma długość 0 lub >2000.
  - Pydantic zgłasza `ValidationError`, mapowane na JSON z `detail.code`.
- 401 Unauthorized: brak/nieprawidłowy JWT, korzystamy z standardowego wyjątku auth.
- 404 Not Found: `meal_id` nie istnieje / nie należy do użytkownika / `deleted_at` ≠ null.
- 409 Conflict: aktywny przebieg dla `meal_id` (status queued/running); odpowiedź zawiera `existing_run_id`.
- 500 Internal Server Error: nieudana transakcja DB lub enqueue; log + opcjonalna aktualizacja `error_code`, `error_message`.

## 8. Rozważania dotyczące wydajności

- Asynchroniczne DB + HTTP klienci; wykorzystywać connection pooling.
- Indeksy Supabase: `(meal_id, status)`, `(user_id, created_at)` oraz unikalny `(meal_id, run_no)`.
- BackgroundTasks/queue zamiast blokowania HTTP.
- Dodanie metryk OTel (czas transakcji, latency kolejki, częstotliwość błędów).
- Ograniczenie pobranych kolumn do potrzebnych; użycie `select` z Supabase.

## 9. Etapy wdrożenia

1. Dodać schematy request/response w `app/api/v1/schemas/analysis_runs.py` z walidacją Pydantic.
2. Rozszerzyć repozytorium `app/db/repositories/analysis_runs.py` o metody `get_meal_for_user`, `get_active_run`, `insert_run`, `next_run_no`.
3. Zaimplementować `AnalysisRunService` z logiką biznesową i integracją z kolejką/background taskiem.
4. Dodać endpoint do routera `app/api/v1/endpoints/analysis_runs.py` (dependency auth, service, response 202).
5. Skonfigurować DI w `app/api/v1/dependencies.py` oraz zarejestrować trasę w `app/api/v1/router.py`.
6. Przygotować adapter pipeline AI (`app/services/ai/analysis_pipeline.py`) aktualizujący `analysis_runs` i `analysis_run_items`.
