# API Endpoint Implementation Plan: GET /api/v1/analysis-runs

## 1. Przegląd punktu końcowego

- Zwraca stronicowaną listę przebiegów analizy dla aktualnego użytkownika w celu obserwacji i raportowania.
- Obsługuje filtrowanie po `meal_id`, `status`, zakresie dat oraz sortowanie (domyślnie malejąco po `created_at`).
- Zapewnia kurso-rową paginację (`page[size]`, `page[after]`) zgodną z konwencją API.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/analysis-runs`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Accept: application/json`
- Parametry (query):
  - Wymagane: brak
  - Opcjonalne:
    - `meal_id` (`UUID4`)
    - `status` (`queued|running|succeeded|failed|cancelled`)
    - `created_from`, `created_to` (`RFC3339 timestamp`)
    - `page[size]` (int 1–50, domyślnie 20)
    - `page[after]` (cursor string base64/opaque)
    - `sort` (np. `-created_at`, `created_at`)
- Body: brak
- Walidacja:
  - Każdy query param walidowany przez Pydantic (UUID, Literal, datetime, int range).
  - Waliduj `created_from <= created_to` (jeśli oba dostarczone).
  - Waliduj `sort` względem whitelisty pól (`created_at`, `run_no`).
  - Waliduj `page[after]` jako poprawny cursor (np. base64 JSON z `created_at`, `id`).

## 3. Wykorzystywane typy

- `AnalysisRunListQuery` (`BaseModel`) opisujący parametry zapytania.
- `Cursor` util (np. `AnalysisRunCursor` dataclass) serializujący/dekodujący `page[after]`.
- `AnalysisRunSummary` (dataclass/TypedDict) zawierający pola listy (`id`, `meal_id`, `run_no`, `status`, `threshold_used`, `model`, `created_at`, `completed_at`).
- `AnalysisRunListResponse` (`BaseModel`) z polami `data: list[AnalysisRunSummaryResponse]`, `page: PageMeta` (`size`, `after`).
- `AnalysisRunRepository.list_runs(query: AnalysisRunListQuery, user_id: UUID)`.
- `AnalysisRunService.list_runs(query, user_id)` implementujący logikę limitu i kursora.
- `PageMeta` schema (reuse w innych endpointach, jeśli istnieje).

## 3. Szczegóły odpowiedzi

- Sukces: `200 OK`
- Struktura JSON:
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
    "page": {
      "size": 20,
      "after": "opaque-cursor"
    }
  }
  ```
- Nagłówki: `Content-Type: application/json; charset=utf-8`; `Cache-Control: private, max-age=15` (opcjonalne).

## 4. Przepływ danych

- Handler pobiera `user_id` z dependency auth i waliduje query paramy poprzez `AnalysisRunListQuery`.
- Deleguje do `AnalysisRunService.list_runs(query, user_id)`.
- Serwis:
  1. Normalizuje `page[size]` (max 50) i `sort`.
  2. Deleguje do repo: buduje zapytanie Supabase z filtrami (`meal_id`, `status`, zakres dat).
  3. Kursory: jeśli `page[after]` obecne, dekoduj do `(created_at, id)` i dodaj warunek > / < zależnie od sortowania.
  4. Dodaje limit `size + 1` dla detekcji następnej strony.
  5. Repo wykonuje `select` ograniczony do potrzebnych kolumn i mapuje wyniki do listy `AnalysisRunSummary`.
  6. Serwis buduje nowy cursor (ostatni rekord) i formuje `PageMeta`.
- Handler serializuje do `AnalysisRunListResponse` i zwraca `200`.

## 5. Względy bezpieczeństwa

- Autentykacja: Supabase JWT.
- Autoryzacja: filtr `user_id` w repo + RLS.
- Walidacja wejścia zapobiega injection (np. wymuszenie whitelisty sortowania, ograniczenie rozmiaru kursora).
- Rate limiting: wprowadzić limit (np. 60 req/min) aby uniknąć nadużyć listingu.
- Logowanie: loguj parametry filtrów w sposób znormalizowany (bez danych wrażliwych).

## 6. Obsługa błędów

- `400 Bad Request`: błędne parametry (zły format UUID, sort spoza listy, `page[size]>50`, błędny cursor).
- `401 Unauthorized`: brak/nieprawidłowy JWT.
- `500 Internal Server Error`: błąd Supabase, dekodowania kursora, nieoczekiwane wyjątki. Loguj z `exc_info` i `query`.
- Kursory nieprawidłowe → `detail.code = "invalid_cursor"`.

## 7. Wydajność

- Indeks `(user_id, created_at DESC)` oraz `(user_id, meal_id, created_at)` przyspiesza filtry.
- Kursory zapewniają stabilną paginację bez offset.
- Ogranicz `select` do wymaganych kolumn, redukując transfer.
- Wspólny klient Supabase (DI) dla pooling.
- Monitoruj metryki (`Counter` liczby pobrań, `Histogram` czasu odpowiedzi, `Gauge` paginated size).

## 8. Kroki implementacji

1. Utwórz `AnalysisRunListQuery` i `AnalysisRunListResponse` w `app/api/v1/schemas/analysis_runs.py`.
2. Zaimplementuj util kursora (np. `app/api/v1/pagination.py`) lub rozbuduj istniejący.
3. Rozszerz `AnalysisRunRepository` o metodę `list_runs` przyjmującą parametry filtrów i kursora.
4. Dodaj `AnalysisRunService.list_runs` zarządzający walidacją biznesową, limitami i generowaniem kursora.
5. Zaimplementuj endpoint w `app/api/v1/endpoints/analysis_runs.py` (`@router.get("/analysis-runs")`).
6. Zaktualizuj router `app/api/v1/router.py` (tag, opis, `responses`).
