# API Endpoint Implementation Plan: GET /api/v1/meal-categories

## 1. Przegląd punktu końcowego

Endpoint udostępnia kanoniczną listę kategorii posiłków (np. `breakfast`, `lunch`) dla interfejsu użytkownika. Zapewnia jednolite etykiety i kolejność wyświetlania, umożliwia lokalizację etykiet oraz przygotowuje obsługę flagi `include_inactive`.

## 2. Szczegóły żądania

- Metoda HTTP: GET
- Struktura URL: `/api/v1/meal-categories`
- Parametry:
  - Wymagane: brak
  - Opcjonalne: `locale` (`Query[str]`, domyślne `pl-PL`, ograniczone regex `^[a-z]{2}-[A-Z]{2}$` i `max_length=5`), `include_inactive` (`Query[bool]`, domyślnie `False`)
- Request Body: brak
- Pydantic DTO (wejściowe): `MealCategoriesQueryParams` z polami `locale` i `include_inactive` (model osadzony w dependency FastAPI).

## 3. Szczegóły odpowiedzi

- Sukces `200 OK`:
  ```
  {
    "data": [
      {"code": "breakfast", "label": "Śniadanie", "sort_order": 1}
    ]
  }
  ```
- Pydantic DTO (wyjściowe):
  - `MealCategoryResponseItem` (`code: str`, `label: str`, `sort_order: int`).
  - `MealCategoriesResponse` (`data: list[MealCategoryResponseItem]`).
- Nagłówki: `Content-Type: application/json; charset=utf-8`.
- Brak paginacji (lista ma niewielki rozmiar, sortowanie deterministyczne).

## 4. Przepływ danych

1. Klient wysyła żądanie z tokenem Supabase JWT i opcjonalnymi parametrami query.
2. FastAPI endpoint w `app/api/v1/endpoints/meal_categories.py` waliduje query przez Pydantic.
3. Endpoint wstrzykuje zależność `get_current_user` dla autoryzacji.
4. Endpoint deleguje do `MealCategoriesService.list_categories(locale, include_inactive)`.
5. Serwis wykorzystuje repozytorium (`MealCategoriesRepository`) łączące się z Supabase (np. `SupabaseClient`) by pobrać rekordy z `public.meal_categories`.
6. Repozytorium wykonuje selekcję kolumn `code`, `label`, `sort_order`, filtruje `active` (gdy kolumna zostanie dodana), stosuje sortowanie rosnące po `sort_order`.
7. Serwis mapuje wyniki na DTO i zwraca do endpointu.
8. Endpoint opakowuje wynik w `MealCategoriesResponse` i zwraca JSON.

## 5. Względy bezpieczeństwa

- Autoryzacja: żądanie wymaga ważnego tokena; użyć dependency `get_current_user`. W przypadku braku tokena FastAPI zwraca `401 Unauthorized`.
- Dostęp do danych: `meal_categories` to słownik globalny; jeśli RLS blokuje odczyt dla ról użytkowników, serwis powinien korzystać z serwisowego klucza Supabase lub materializowanego widoku udostępnionego klientom.
- Walidacja danych wejściowych: Pydantic zatrzymuje niepoprawne `locale` (regex). `include_inactive` przyjmuje tylko wartości boolowskie.
- Brak danych wrażliwych; mimo to unikamy logowania parametrów zapytań wrażliwych (tu bez znaczenia).

## 6. Obsługa błędów

- `400 Bad Request`: Błąd walidacji (np. niepoprawny format `locale`). FastAPI domyślnie zwraca `422`, można dostosować handler do mapowania na `400` zgodnie z polityką API.
- `401 Unauthorized`: Brak ważnego tokena; zapewnia `HTTPException(status_code=401)`.
- `500 Internal Server Error`: Nieoczekiwane błędy Supabase/DB. Przechwycić ogólne wyjątki, zalogować przez `structlog`/Sentry i zmapować na `HTTPException(500)`.
- Brak `404` (lista może być pusta, co nie jest błędem).

## 7. Wydajność

- Tabela słownikowa ma niewielki rozmiar; pojedyncze zapytanie SELECT z indeksem na `sort_order` jest wystarczająco szybkie.

## 8. Kroki implementacji

1. Utwórz plik endpointu `app/api/v1/endpoints/meal_categories.py` z routerem FastAPI i konfiguracją parametrów query.
2. Zarejestruj router w `app/api/v1/router.py` (`api_router.include_router(..., prefix="/meal-categories", tags=["meal-categories"])`).
3. Dodaj modele Pydantic do `app/api/v1/schemas/meal_categories.py`.
4. Utwórz serwis `MealCategoriesService` w `app/services/meal_categories.py` wraz z interfejsem repozytorium.
5. Dodaj repozytorium `MealCategoriesRepository` w `app/db/repositories/meal_categories.py` korzystające z klienta Supabase i obsługę RLS.
6. Zaimplementuj dependency injection dla serwisu (np. `get_meal_categories_service`).
7. Dodaj obsługę logowania błędów i mapowania wyjątków (np. custom `DatabaseError` -> 500).
