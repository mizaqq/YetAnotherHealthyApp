# API Endpoint Implementation Plan_1: GET /api/v1/meals

## 1. Przegląd punktu końcowego

- Zwraca paginowaną listę posiłków użytkownika z możliwością filtrowania po dacie, kategorii, źródle oraz usuniętych rekordach.
- Wspiera sortowanie chronologiczne oraz stronicowanie kursorem, przygotowując dane do widoków historii i raportów.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/meals`
- Nagłówki: `Authorization: Bearer <JWT>`
- Parametry:
  - Wymagane: brak
  - Opcjonalne query params: `from`, `to`, `category`, `source`, `include_deleted`, `page[size]`, `page[after]`, `sort`
- Walidacje wejścia:
  - `from`/`to` jako daty (ISO8601) z kontrolą, że `from` ≤ `to`
  - `category` istniejące w `meal_categories.code`
  - `source` ∈ {`ai`, `edited`, `manual`}
  - `include_deleted` bool (default `false`)
  - `page[size]` 1..100, `page[after]` jako poprawny cursor (np. Base64/UUID)
  - `sort` ograniczone do `eaten_at`, `-eaten_at`
- Modele wejściowe:
  - `MealListQuery` (Pydantic) normalizujące parametry i zapewniające walidację zakresów

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `200 OK`
- Struktura body:
  - `data`: lista elementów `{id, category, eaten_at, calories, protein, fat, carbs, source, accepted_analysis_run_id}`
  - `page`: `{size, after}` jako cursor do kolejnej strony
- Modele wyjściowe:
  - `MealListItem` dla elementów listy
  - `MealListResponse` zawierający kolekcję i metadane stronicowania

## 4. Przepływ danych

- Autoryzacja JWT → `get_current_user` pobiera `user_id`.
- FastAPI mapuje parametry do `MealListQuery` i przekazuje `MealService.list_meals` wraz z sesją bazy Supabase.
- Serwis buduje zapytanie uwzględniające filtry, `include_deleted`, sortowanie oraz kursor (`LIMIT page[size] + 1`).
- Serwis konwertuje wynik do DTO, generuje kolejny cursor (`page[after]`) i zwraca strukturę `MealListResponse`.
- Handler serializuje odpowiedź i zwraca z kodem 200.

## 5. Względy bezpieczeństwa

- Weryfikacja JWT wymagana dla każdej operacji; `user_id` z tokena.
- Filtry i kursory ograniczone do zasobów użytkownika (WHERE `user_id` = current).
- Zapytania parametryzowane przez warstwę repozytorium opartej na kliencie Supabase.
- Odrzucanie nieobsługiwanych pól sortujących zapobiega SQL injection przez nazwę kolumny.

## 6. Obsługa błędów

- `400 Bad Request`: błędny zakres dat, niepoprawny cursor, wartość `page[size]` poza zakresem.
- `401 Unauthorized`: brak/niepoprawny token.
- `500 Internal Server Error`: błędy repozytorium, konwersji kursora; logowane globalnie i (opcjonalnie) w tabeli błędów.

## 7. Wydajność

- Użyć indeksów na `meals.user_id`, `meals.eaten_at`, `meals.category`, `meals.source` dla filtrowania.
- Stosować paginację kursorem zamiast offsetu dla stabilności przy rosnących danych.
- Limitowane kolumny w `SELECT` (tylko potrzebne do listy) redukują transfer.
- Opcjonalna warstwa cache (np. HTTP cache ETag) dla częstych zapytań bez parametrów.

## 8. Kroki implementacji

1. Zdefiniować `MealListQuery`, `MealListItem`, `MealListResponse` w `schemas/meals.py`.
2. Dodać metodę serwisową `MealService.list_meals` obsługującą filtry, kursor, sortowanie.
3. Rozszerzyć repozytorium o zapytania listujące z ograniczeniami `user_id` i generacją kursora.
4. Utworzyć handler FastAPI `get_meals` (GET) z injekcją `MealService`, `CurrentUser`, klienta Supabase.
5. Mapować wyjątki (`InvalidCursorError`, `CategoryNotFoundError`) na odpowiedzi HTTP.
6. Przygotować testy jednostkowe (walidacja query) oraz integracyjne (paginacja, filtry).
7. Zaktualizować dokumentację OpenAPI i plany `.ai` w sekcji listowania posiłków.
