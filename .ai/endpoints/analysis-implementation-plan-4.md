# API Endpoint Implementation Plan: POST /api/v1/analysis-runs/{run_id}/retry

## 1. Przegląd punktu końcowego

- Pozwala ponownie wykonać analizę na podstawie poprzedniego przebiegu (`run_id`) i przechowywanego `raw_input` w ramach jednego, synchronicznego żądania.
- Tworzy nowy wpis w `analysis_runs` z `run_no` inkrementowanym w ramach tego samego posiłku lub kontekstu oraz natychmiast przetwarza wyniki.
- Umożliwia modyfikację progu (`threshold`) i opcjonalny override surowego wejścia; wynik końcowy (sukces/porażka) zwracany jest w odpowiedzi HTTP.

## 2. Szczegóły żądania

- Metoda HTTP: POST
- Struktura URL: `/api/v1/analysis-runs/{run_id}/retry`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Content-Type: application/json`, `Accept: application/json`
- Parametry:
  - Wymagane path: `run_id` (UUID4)
- Body JSON:
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
- Walidacja:
  - `run_id` jako UUID4.
  - `threshold` opcjonalny; jeśli podano → [0,1], domyślnie użyj wartości z poprzedniego przebiegu.
  - `raw_input` opcjonalny; jeśli brak → użyj `analysis_runs.raw_input` z poprzedniego przebiegu.
  - Jeśli dostarczony `raw_input`, waliduj strukturę JSON (np. `text` 1–2000 znaków).
  - Sprawdź, że poprzedni przebieg należy do użytkownika i jest w stanie terminalnym (succeeded/failed/cancelled).
  - Zapewnij brak aktywnej analizy dla powiązanego posiłku.

## 3. Wykorzystywane typy

- `AnalysisRunRetryRequest` (`BaseModel`) z polami `threshold: condecimal(gt=0, lt=1) | None`, `raw_input: dict | None` oraz walidatorami.
- `AnalysisRunRetryResponse` (`BaseModel`) odwzorowujący finalny stan (reuse `AnalysisRunDetailResponse`, które zawiera `model`).
- `RetryAnalysisRunCommand` (dataclass) zawierający `user_id`, `source_run`, `raw_input`, `threshold`.
- `AnalysisRunService.retry_run(command)` zwracający finalny rekord.
- `AnalysisRunRepository` metody: `get_run_by_id`, `get_active_run_by_meal`, `next_run_no`, `insert_run`, `update_status`, `replace_output`.
- `AnalysisRunProcessor` (ten sam co w create) wykonujący analizę synchronicznie; adapter AI w MVP pozostaje mockiem.
- `RunStateValidator` helper (opcjonalnie) upewniający się, że stan źródłowego przebiegu pozwala na retry.

## 3. Szczegóły odpowiedzi

- Sukces: `200 OK`
- Body: kompletne dane nowego przebiegu (status `succeeded`/`failed`/`cancelled`), np.:
  ```json
  {
    "id": "uuid",
    "meal_id": "uuid",
    "run_no": 3,
    "status": "succeeded",
    "latency_ms": 9800,
    "tokens": 2100,
    "cost_minor_units": 28,
    "cost_currency": "USD",
    "threshold_used": 0.75,
    "retry_of_run_id": "uuid",
    "error_code": null,
    "error_message": null,
    "created_at": "2025-10-12T07:55:00Z",
    "completed_at": "2025-10-12T07:55:10Z"
  }
  ```
- Nagłówki: `Content-Type: application/json; charset=utf-8`
- Błędy: `400`, `401`, `404`, `409`, `500`.

## 4. Przepływ danych

- Handler weryfikuje path `run_id`, parsuje body, pobiera `user_id`.
- `AnalysisRunService.retry_run`:
  1. Repo pobiera poprzedni przebieg (`get_run_by_id(run_id, user_id)`), łącznie z `meal_id`, `raw_input`, `status`, `threshold_used`.
  2. Waliduje stan (`status` nie w {queued, running}); brak rekordu → `NotFound`.
  3. Określa docelowy `meal_id` oraz `user_id` (z repo).
  4. Sprawdza aktywny przebieg dla tego `meal_id` (`get_active_run_by_meal`).
  5. Ustala `threshold_used` = request.threshold or previous.threshold.
  6. Ustala `raw_input` = request.raw_input or previous.raw_input; merge override (jeśli potrzebne).
  7. Wylicza `run_no` = previous.run_no + 1 (lub repo `next_run_no`).
  8. Tworzy nowy rekord `analysis_runs` (status początkowy `queued`, `retry_of_run_id` = source `id`) i zapisuje go.
  9. Wywołuje synchronicznie `AnalysisRunProcessor.process(new_run)` (adapter AI = mock):
     - Aktualizuje status na `running`.
     - Uruchamia inferencję, tworzy `analysis_run_items`, zapisuje `raw_output`.
     - Ustawia finalny status (`succeeded` lub `failed`), metryki i `completed_at`.
  10. Zwraca finalny obiekt domenowy do handlera.
- Handler serializuje wynik do `AnalysisRunRetryResponse` i zwraca `200`.

## 5. Względy bezpieczeństwa

- Autentykacja i autoryzacja: weryfikacja `user_id` i RLS.
- Kontrola dostępu do `run_id` tylko dla właściciela.
- Walidacja: ochrona przed injekcją w `raw_input` (np. schema vs. dowolny JSON, min/max length).
- Rate limiting: ogranicz liczbę retry (np. 10/min) by chronić model.
- Audit logging: loguj `run_id`, `new_run_id`, `threshold_used`.

## 6. Obsługa błędów

- `400 Bad Request`: niewłaściwa struktura `raw_input`, `threshold` poza zakresem, stan źródłowego przebiegu nie pozwala na retry.
- `401 Unauthorized`: brak/invalid JWT.
- `404 Not Found`: `run_id` nie istnieje lub nie należy do użytkownika.
- `409 Conflict`: aktywny przebieg dla `meal_id` (queued/running).
- `500 Internal Server Error`: błąd Supabase / kolejki; rozważ oznaczenie nowego przebiegu jako `failed` jeśli enqueue nie powiedzie się po insercie.
- Detale błędów w formacie `{"code": "analysis_run_conflict", "message": "..."}`.

## 7. Wydajność

- Odczyty i wstawki wykorzystują indeksy `(user_id, id)` oraz `(meal_id, run_no)`.
- Reużyj poprzednie `raw_input` aby uniknąć nadmiarowych odczytów.
- Synchroniczne przetwarzanie wydłuża czas requestu – komunikuj UI oczekiwany czas, rozważ timeouty.
- Monitoruj liczbę retry (`Counter`), pełny czas obróbki (`Histogram`), liczbę błędów.

## 8. Kroki implementacji

1. Dodaj `AnalysisRunRetryRequest` oraz `AnalysisRunRetryResponse` (reuse `AnalysisRunDetailResponse`) w `app/api/v1/schemas/analysis_runs.py`.
2. Rozszerz `AnalysisRunRepository` o metody wspierające synchroniczne przetwarzanie (`next_run_no`, `insert_run`, `update_status`, `replace_output`).
3. Dodaj `RetryAnalysisRunCommand` i rozbuduj `AnalysisRunService.retry_run` o logikę synchroniczną wraz z `AnalysisRunProcessor` (mock AI w MVP).
4. Zaimplementuj endpoint w `app/api/v1/endpoints/analysis_runs.py` (`@router.post("/analysis-runs/{run_id}/retry")`) zwracający finalny wynik i status 200.
5. Zaktualizuj router (`responses`, docstring, tag) oraz dokumentację `.ai/api-plan.md` jeśli zmieni się spec.
