# API Endpoint Implementation Plan: GET /api/v1/analysis-runs/{run_id}

## 1. Przegląd punktu końcowego

- Zapewnia szczegółowy widok pojedynczego przebiegu analizy AI powiązanego z zalogowanym użytkownikiem.
- Udostępnia metadane pomiarowe (latency, tokens, koszty), statusy oraz informacje diagnostyczne (`error_code`, `error_message`).
- Służy klientowi frontend do renderowania historii i debugowania wyników analizy bez potrzeby bezpośredniego dostępu do surowych logów backendu.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/analysis-runs/{run_id}`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Accept: application/json`
- Parametry:
  - Wymagane: `run_id` (UUID4 w ścieżce)
  - Opcjonalne: brak
- Body: brak
- Walidacja wejścia:
  - Path param walidowany jako `UUID4`; błędne wartości → `400` z kodem `invalid_run_id`.
  - JWT weryfikowany przez dependency auth; brak lub niepoprawny token → `401`.
- Wykorzystywane typy (DTO / Command):
- `AnalysisRunDetailResponse` (`pydantic.BaseModel`) z polami `id`, `meal_id`, `run_no`, `status`, `latency_ms`, `tokens`, `cost_minor_units`, `cost_currency`, `threshold_used`, `model`, `retry_of_run_id`, `error_code`, `error_message`, `created_at`, `completed_at`.
  - `AnalysisRunStatus` (Literal lub Enum) wspólne dla request/response.
- `AnalysisRunDetail` (dataclass/TypedDict) jako obiekt domenowy w serwisie.
- `AnalysisModelProvider` (np. `app/core/config.py`) dostarczający stały identyfikator modelu używany przez wszystkie przebiegi.
  - `AnalysisRunRepository` (metoda `get_by_id`) oraz `AnalysisRunService.get_run_detail` (nowa lub rozszerzona).

## 3. Szczegóły odpowiedzi

- Sukces: `200 OK`
- Struktura JSON:
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
    "model": "openrouter/gpt-4o-mini",
    "retry_of_run_id": "uuid",
    "error_code": "TIMEOUT",
    "error_message": "Model response exceeded limit",
    "created_at": "2025-10-12T07:40:00Z",
    "completed_at": "2025-10-12T07:40:11Z"
  }
  ```
- Nagłówki: `Content-Type: application/json; charset=utf-8`; opcjonalnie `Cache-Control: private, max-age=30` dla krótkiej pamięci podręcznej UI.
- Brak paginacji / metadanych listy (pojedynczy zasób).

## 4. Przepływ danych

- `get_current_user` (dependency FastAPI) weryfikuje JWT Supabase, zwraca `user_id`.
- Handler endpointu parsuje `run_id` jako `UUID4`, wywołuje `AnalysisRunService.get_run_detail(run_id, user_id)`.
- Serwis:
  1. Deleguje do `AnalysisRunRepository.get_by_id(run_id, user_id)` z selektem ograniczonym do wymaganych kolumn.
  2. Repo korzysta z Supabase client: `supabase.table("analysis_runs").select(<kolumny>).eq("id", run_id).eq("user_id", user_id).limit(1)`.
  3. Brak rekordu → zwraca `None`; obecny rekord mapuje do `AnalysisRunDetail` (konwersja typów Decimal → float, timestamp → `datetime`).
  4. Serwis loguje audyt (`logger.info("analysis_runs.view", extra={...})`) i zwraca dane.
- Handler serializuje wynik do `AnalysisRunDetailResponse` i zwraca `200`.
- Brak modyfikacji danych; analiza błędów korzysta z pól `error_code`/`error_message` w tabeli `analysis_runs`, więc nie wymaga osobnej tabeli błędów.

## 5. Względy bezpieczeństwa

- Autentykacja: wyłącznie autoryzowani użytkownicy (Supabase JWT); endpoint nie jest publiczny.
- Autoryzacja: filtry `user_id` + Supabase RLS na `analysis_runs` zapewniają brak dostępu między użytkownikami.
- Walidacja danych: wczesne odrzucenie nieprawidłowych UUID ogranicza wektor DoS (uniknięcie pełnego zapytania do Supabase).
- Ekspozycja danych: odpowiedź ograniczona do metadanych; brak wrażliwych pól (`raw_input`, `raw_output`).
- Rate limiting / throttling: wykorzystać istniejący limiter (jeśli dostępny) lub ustalić limit 60 req/min na użytkownika.
- Monitoring dostępu: logi strukturalne bez wrażliwych danych; uwzględnić `request_id` dla korelacji.

## 6. Obsługa błędów

- `400 Bad Request`: path param nie jest UUID; zwróć `{"code": "invalid_run_id", "message": "run_id must be a valid UUID"}`.
- `401 Unauthorized`: brak lub nieprawidłowy JWT (obsługiwane przez dependency); komunikat `{"code": "unauthorized"}`.
- `404 Not Found`: Supabase zwraca brak rekordu (nie istnieje lub należy do innego użytkownika); mapa do `HTTPException(status_code=404, detail={"code": "analysis_run_not_found"})`.
- `500 Internal Server Error`: nieprzewidziane błędy repo/serwisu (np. błąd sieci Supabase); logować stack trace i zwracać `{"code": "internal_error"}`.
- Logowanie błędów: `logger.error` z `exc_info=True`, `run_id`, `user_id`, `trace_id`; dodatkowo, jeśli posiadamy tabelę diagnostyczną w przyszłości, przewidziane jest rozszerzenie serwisu o zapis do niej, na dziś wykorzystujemy pola `analysis_runs.error_*`.

## 7. Wydajność

- Ograniczenie selektu do niezbędnych kolumn minimalizuje transfer JSON.
- Reużyj wspólny klient Supabase (DI), aby korzystać z pooling i keep-alive.

## 8. Kroki implementacji

1. Dodaj `AnalysisRunDetailResponse` i `AnalysisRunStatus` do `app/api/v1/schemas/analysis_runs.py` z dokładnymi typami (`UUID4`, `Literal`, `datetime`), ustawiając `ConfigDict(from_attributes=True)`.
2. Rozszerz `AnalysisRunRepository` (`app/db/repositories/analysis_runs.py`) o metodę `get_by_id` filtrującą po `user_id` i mapującą rekordy Supabase.
3. Utwórz/rozszerz `AnalysisRunService` (`app/services/analysis_runs.py`) dodając `get_run_detail`; obsłuż `None` → `NotFoundError`.
4. Zaimplementuj endpoint w `app/api/v1/endpoints/analysis_runs.py`: dekorator `@router.get("/analysis-runs/{run_id}")`, wstrzyknięcie `AnalysisRunService`, mapowanie wyjątków do `HTTPException`.
5. Zarejestruj trasę w `app/api/v1/router.py` (tag `Analysis Runs`, opis, spec `responses`).
