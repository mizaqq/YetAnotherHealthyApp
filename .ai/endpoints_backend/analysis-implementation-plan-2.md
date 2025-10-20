# API Endpoint Implementation Plan: POST /api/v1/analysis-runs

## 1. Przegląd punktu końcowego

- Kolejkuje nowy przebieg analizy AI dla posiłku użytkownika lub surowego opisu tekstowego.
- Tworzy wpis w tabeli `analysis_runs` i natychmiast uruchamia proces analizy w ramach tego samego żądania (brak event buffer / kolejki w MVP).
- Zapewnia kontrolę równoległych analiz (limit jednej aktywnej analizy na posiłek) oraz przechowuje surowe wejście do ewentualnego retry.

## 2. Szczegóły żądania

- Metoda HTTP: POST
- Struktura URL: `/api/v1/analysis-runs`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Content-Type: application/json`, `Accept: application/json`
- Parametry:
  - Wymagane: brak (poza autoryzacją)
  - Opcjonalne: brak
- Body JSON:
  ```json
  {
    "meal_id": "uuid | null",
    "input_text": "Owsianka z bananem i miodem",
    "threshold": 0.8
  }
  ```
- Walidacja:
  - Wymagaj co najmniej jednego z `meal_id`, `input_text`.
  - `input_text`: po `strip` długość 1–2000 znaków, usuń znaki kontrolne.
  - `meal_id`: `UUID4`; potwierdź istnienie posiłku, własność (`user_id`), brak `deleted_at`.
  - `threshold`: liczba zmiennoprzecinkowa w [0,1]; domyśl 0.8.
  - Wykryj aktywny (queued/running) przebieg dla `meal_id` → `409 Conflict`.

## 3. Wykorzystywane typy

- `AnalysisRunCreateRequest` (`BaseModel`) z walidatorami zależności pól.
- `AnalysisRunQueuedResponse` (`BaseModel`) dla odpowiedzi 202.
- `CreateAnalysisRunCommand` (dataclass) przenoszący `user_id`, `meal`, `raw_input`, `threshold`, `source`, `retry_of_run_id`.
- `AnalysisRunService` metoda `create_run(command)` oraz `process_run(run: AnalysisRun)` uruchamiana synchronicznie.
- `AnalysisModelProvider` (np. `app/core/config.py`) udostępniający stały identyfikator modelu używany w każdym przebiegu.
- `AnalysisRunRepository` metody: `get_meal_for_user`, `get_active_run`, `next_run_no`, `insert_run`, `update_status`, `replace_output`.
- `AnalysisRunProcessor` (nowy serwis domenowy) odpowiedzialny za wykonanie analizy i zapis `analysis_run_items` bezpośrednio.
- `MealRepository` (jeśli istnieje) do walidacji posiłku.

## 3. Szczegóły odpowiedzi

- Sukces: `202 Accepted`
- Struktura JSON:
  ```json
  {
    "id": "uuid",
    "meal_id": "uuid|null",
    "run_no": 1,
    "status": "queued",
    "threshold_used": 0.8,
    "model": "openrouter/gpt-4o-mini",
    "retry_of_run_id": null,
    "latency_ms": null,
    "created_at": "2025-10-12T07:29:30Z"
  }
  ```
- Nagłówki: `Location: /api/v1/analysis-runs/{id}`, `Retry-After: 5`, `Content-Type: application/json; charset=utf-8`.
- Błędy: `400`, `401`, `404`, `409`, `500`.

## 4. Przepływ danych

- `get_current_user` dependency zwraca `user_id`.
- Handler waliduje payload, buduje `CreateAnalysisRunCommand` (uzupełnienie default threshold, normalizacja tekstu).
- `AnalysisRunService.create_run`:
  1. Jeśli `meal_id` → repozytorium pobiera posiłek i weryfikuje właściciela.
  2. Repo sprawdza aktywny przebieg (`status` ∈ {queued, running}).
  3. Wyznacza `run_no` (1 + max istniejący dla danego posiłku).
  4. Składa rekord `analysis_runs` (status początkowy `queued`, `raw_input`, `threshold_used`, `model` z konfiguracji) i wstawia go do Supabase.
  5. Natychmiast wywołuje `AnalysisRunProcessor.process(run)` (synchronicznie), który:
     - Aktualizuje status na `running`.
     - Woła adapter AI, otrzymuje wynik, przelicza `analysis_run_items` i zapisuje je.
     - Adapter AI na ten moment powinien być Mockiem
     - Aktualizuje rekord `analysis_runs` (`status`, `raw_output`, metryki, `completed_at`).
     - W przypadku błędu ustawia `status=failed` i zapisuje `error_code`, `error_message`.

## 5. Względy bezpieczeństwa

- Autentykacja: Supabase JWT.
- Autoryzacja: wszystkie zapytania repo filtrują po `user_id`; Supabase RLS dodatkowo egzekwuje.
- Walidacja: kontrola długości i sanitizacja `input_text` (normalizacja whitespace, usunięcie znaków kontrolnych).
- Rate limiting: zastosuj istniejący limiter (np. 20 żądań/min), by chronić zasoby AI.
- Logging: loguj `run_id`, `user_id`, `meal_id` (jeśli obecne) bez surowego tekstu.
- Ochrona przed prompt injection: przechowuj `raw_input` w JSON bez reinterpretacji w logach.

## 6. Obsługa błędów

- `400 Bad Request`: brak `meal_id` i `input_text`, zbyt krótki/długi tekst, niepoprawny `threshold`, błędne UUID.
- `401 Unauthorized`: brak/niepoprawne JWT.
- `404 Not Found`: `meal_id` nie istnieje lub nie należy do użytkownika.
- `409 Conflict`: istnieje aktywny przebieg dla `meal_id`.
- `500 Internal Server Error`: błąd Supabase / kolejki; logowanie z `exc_info`. W razie błędu po insercie i przed kolejką rozważyć aktualizację rekordu `status` na `failed` z `error_code`.
- Odpowiedzi z `detail` zawierają `code` (np. `analysis_run_active`), `message`.

## 7. Rozważania dotyczące wydajności

- Wstawki i selekty targetowane po indeksach `(meal_id, status)` oraz `(user_id, created_at)`.
- Reużyj pojedynczego klienta Supabase (DI) dla connection pooling.

## 8. Kroki implementacji

1. Dodaj `AnalysisRunCreateRequest` i `AnalysisRunQueuedResponse` w `app/api/v1/schemas/analysis_runs.py` z walidatorami Pydantic.
2. Rozszerz `AnalysisRunRepository` o metody walidujące posiłek, aktywne przebiegi i tworzenie/aktualizację rekordów (`insert_run`, `update_status`, `replace_output`).
3. Zaimplementuj `CreateAnalysisRunCommand` oraz synchroniczną logikę `AnalysisRunService.create_run` + `AnalysisRunProcessor` wykonującą analizę bezpośrednio.
4. Dodaj adapter AI (`app/services/ai/analysis_processor.py`) realizujący wywołanie modelu oraz zapis wyników.
5. Dodaj endpoint w `app/api/v1/endpoints/analysis_runs.py` (handler POST) wraz z dependency injection serwisu, mapowaniem wyjątków na `HTTPException`.
6. Rozszerz router `app/api/v1/router.py` o trasę POST i odpowiednie `responses`.
