# API Endpoint Implementation Plan_2: GET /api/v1/meals/{meal_id}

## 1. Przegląd punktu końcowego

- Zwraca szczegółowe dane pojedynczego posiłku wraz z powiązaną akceptowaną analizą (opcjonalnie listą pozycji).
- Pozwala aplikacji frontend na wyświetlenie kontekstu makroelementów oraz historii zmian posiłku.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/meals/{meal_id}`
- Nagłówki: `Authorization: Bearer <JWT>`
- Parametry:
  - Wymagane path param: `meal_id` (UUID)
  - Opcjonalne query param: `include_analysis_items` (bool, domyślnie `false`)
- Walidacje wejścia:
  - `meal_id` poprawny UUID
  - `include_analysis_items` parser bool (np. `true/false/1/0`)
- Modele wejściowe:
  - `MealDetailParams` (Pydantic) agregujący `meal_id`, `include_analysis_items`

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `200 OK`
- Struktura body:
  - Podstawowe pola posiłku (`id`, `user_id`, `category`, `eaten_at`, `source`, makra, `accepted_analysis_run_id`, `created_at`, `updated_at`)
  - Sekcja `analysis` zawierająca `run` (`id`, `status`, `run_no`) oraz `items` jeśli `include_analysis_items=true`
- Modele wyjściowe:
  - `MealDetailResponse` z zagnieżdżonym `MealAnalysisRun` i opcjonalną listą `MealAnalysisItem`

## 4. Przepływ danych

- Autoryzacja JWT → `get_current_user` dostarcza `user_id`.
- FastAPI waliduje parametry przez `MealDetailParams` i przekazuje do `MealService.get_meal_detail` wraz z sesją bazy Supabase.
- Serwis pobiera posiłek użytkownika (`WHERE id = :meal_id AND user_id = :current`), uwzględniając `deleted_at` jeśli ±.
- Jeśli istnieje `accepted_analysis_run_id`, serwis pobiera dane analizy; gdy `include_analysis_items=true`, dołącza elementy z `analysis_run_items`.
- Serwis mapuje wynik do `MealDetailResponse`; brak rekordu → wyjątek `MealNotFoundError`.
- Handler zwraca JSON z kodem 200.

## 5. Względy bezpieczeństwa

- Weryfikacja JWT wymagająca autoryzacji.
- Zapytania ograniczone `user_id` = current user, eliminują dostęp do cudzych posiłków.
- Parametryzowane zapytania/ODBC w repozytorium.
- Warunkowe ładowanie `analysis_items` zabezpiecza przed nadmiernym ujawnieniem danych.

## 6. Obsługa błędów

- `400 Bad Request`: niepoprawny UUID `meal_id`, niewłaściwa wartość `include_analysis_items`.
- `401 Unauthorized`: brak/niepoprawny token.
- `404 Not Found`: posiłek nie istnieje lub nie należy do użytkownika; analiza brakująca przy żądaniu szczegółowych danych.
- `500 Internal Server Error`: błędy repozytorium, mapowania; logowane i opcjonalnie rejestrowane w tabeli błędów.

## 7. Wydajność

- Indeks `meals.id` oraz `analysis_runs.id` zapewnia szybkie wyszukiwanie.
- Warunkowe ładowanie `analysis_items` zapobiega zbędnym joinom.
- Możliwość cache (np. CDN + ETag) dla niezmiennych danych posiłków.
- Optymalizacja zapytań: wykorzystywać `SELECT` z enumeracją kolumn, ograniczyć `JOIN` tylko gdy wymagane.

## 8. Kroki implementacji

1. Zdefiniować `MealDetailParams`, `MealDetailResponse`, `MealAnalysisRun`, `MealAnalysisItem` w `schemas/meals.py`.
2. Dodać metodę `MealService.get_meal_detail` łączącą dane posiłku i analizy.
3. W repozytorium przygotować zapytania do `meals`, `analysis_runs`, `analysis_run_items` z filtrami po `user_id`.
4. Utworzyć handler FastAPI `get_meal_detail` (GET) pobierający parametry i zwracający `MealDetailResponse`.
5. Mapować wyjątki (`MealNotFoundError`, `AnalysisNotFoundError`) na odpowiedzi HTTP 404/500.
6. Przygotować testy jednostkowe walidacji parametrów oraz integracyjne (szczegóły z/bez `analysis_items`).
7. Uaktualnić dokumentację OpenAPI, README oraz plan `.ai` dla widoku szczegółowego posiłku.
