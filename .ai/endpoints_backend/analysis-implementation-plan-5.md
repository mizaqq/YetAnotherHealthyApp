# API Endpoint Implementation Plan: GET /api/v1/analysis-runs/{run_id}/items

## 1. Przegląd punktu końcowego

- Zwraca listę składników (`analysis_run_items`) wygenerowanych w ramach wskazanego przebiegu analizy.
- Dostarcza szczegóły ilościowe (masa, makroelementy, confidence) do wyświetlenia w UI i dalszych obliczeń.
- Zapewnia wgląd tylko właścicielowi przebiegu dzięki Supabase JWT + RLS.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/analysis-runs/{run_id}/items`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Accept: application/json`
- Parametry:
  - Path (wymagane): `run_id` (`UUID4`)
  - Query: brak w MVP (brak paginacji; liczba składników niewielka)
- Body: brak
- Walidacja wejścia:
  - `run_id` jako `UUID4`; w przypadku błędu → `400 Bad Request` z kodem `invalid_run_id`.
  - Autoryzacja odbywa się poprzez dependency auth; brak/niepoprawny token → `401`.
  - Serwis weryfikuje, że przebieg należy do `user_id`; brak rekordu → `404`.

## 3. Wykorzystywane typy

- `AnalysisRunItemsResponse` (`BaseModel`) zawierający pola `run_id: UUID4`, `model: str`, `items: list[AnalysisRunItemResponse]`.
- `AnalysisRunItemResponse` (`BaseModel`) z polami: `id`, `ordinal`, `raw_name`, `raw_unit`, `quantity`, `unit_definition_id`, `product_id`, `product_portion_id`, `weight_grams`, `confidence`, `calories`, `protein`, `fat`, `carbs`.
- `AnalysisRunItem` (dataclass/TypedDict) w warstwie domenowej.
- `AnalysisRunRepository.get_run_by_id(run_id, user_id)` (reuse) do weryfikacji własności.
- `AnalysisRunItemsRepository.list_items(run_id, user_id)` (nowa metoda) zwracająca posortowane składniki.
- `AnalysisRunService.get_run_items(run_id, user_id)` łączący walidację runu i pobranie składników.

## 3. Szczegóły odpowiedzi

- Sukces: `200 OK`
- Struktura JSON:
  ```json
  {
    "run_id": "uuid",
    "model": "openrouter/gpt-4o-mini",
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
- Nagłówki: `Content-Type: application/json; charset=utf-8`.
- W przypadku braku składników zwróć pustą listę (status 200).

## 4. Przepływ danych

- Dependency `get_current_user` zwraca `user_id`.
- Handler waliduje `run_id`, wywołuje `AnalysisRunService.get_run_items`.
- Serwis:
  1. Używa `AnalysisRunRepository.get_run_by_id` w celu potwierdzenia istnienia runu i prawa dostępu.
  2. Jeżeli przebieg nie istnieje → `NotFoundError`.
  3. Wywołuje `AnalysisRunItemsRepository.list_items(run_id, user_id)` (select ograniczony do wymaganych kolumn, sortowanie po `ordinal`).
  4. Mapuje rekordy do `AnalysisRunItem` i zwraca strukturę (`run_id`, `items`).
- Handler serializuje wynik do `AnalysisRunItemsResponse` i zwraca `200`.
- Logowanie: `logger.info("analysis_runs.items", extra={"run_id": run_id, "items_count": len(items)})`.

## 5. Względy bezpieczeństwa

- Autentykacja: Supabase JWT jest obowiązkowy.
- Autoryzacja: zapytania repozytorium zawsze filtrują po `user_id`, RLS zapewnia dodatkowe zabezpieczenie.
- Walidacja: wczesne sprawdzenie UUID ogranicza błędy Supabase.
- Dane wrażliwe: brak surowego wejścia; ekspozycja ograniczona do danych żywieniowych.
- Rate limiting: reuse globalnego limitera (np. 60 req/min na użytkownika).

## 6. Obsługa błędów

- `400 Bad Request`: niepoprawny `run_id` (nie-UUID).
- `401 Unauthorized`: brak/nieprawidłowy token.
- `404 Not Found`: przebieg nie istnieje lub nie należy do użytkownika.
- `500 Internal Server Error`: błąd Supabase lub nieoczekiwany wyjątek; loguj `exc_info` i `run_id`.
- Konwencja detail: `{"code": "analysis_run_not_found", "message": "..."}` itp.

## 7. Rozważania dotyczące wydajności

- Wykorzystaj indeks `(run_id, ordinal)` na `analysis_run_items` zapewniający sortowanie.
- Ogranicz `select` do niezbędnych kolumn.
- Możliwość cache na poziomie aplikacji (krótko żyjące) jeśli endpoint odpytywany wielokrotnie.
- Monitoruj metryki (`Histogram` czasu odpowiedzi, `Gauge` średniej liczby składników) w celu oceny konieczności paginacji w przyszłości.

## 8. Kroki implementacji

1. Dodaj schematy `AnalysisRunItemResponse` i `AnalysisRunItemsResponse` w `app/api/v1/schemas/analysis_runs.py`.
2. Rozbuduj repozytorium `analysis_runs` lub utwórz dedykowane `analysis_run_items_repository` z metodą `list_items`.
3. Dodaj do `AnalysisRunService` metodę `get_run_items` z walidacją własności.
4. Zaimplementuj endpoint w `app/api/v1/endpoints/analysis_runs.py` (`@router.get("/analysis-runs/{run_id}/items")`).
5. Zaktualizuj router główny (`app/api/v1/router.py`) o nową trasę i dokumentację `responses`.
