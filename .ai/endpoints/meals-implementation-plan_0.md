# API Endpoint Implementation Plan: POST /api/v1/meals

## 1. Przegląd punktu końcowego

- Tworzy nowy wpis posiłku powiązany z zalogowanym użytkownikiem, obsługując źródła `ai`, `edited`, `manual`.
- Zapewnia spójność makroelementów z ograniczeniami tabeli `public.meals` oraz powiązanie z rekordami `analysis_runs` i `meal_categories`.
- Udostępnia dane do raportów historii posiłków oraz dalszych analiz żywieniowych.

## 2. Szczegóły żądania

- Metoda HTTP: POST
- Struktura URL: `/api/v1/meals`
- Nagłówki: `Authorization: Bearer <JWT>`, `Content-Type: application/json`
- Parametry:
  - Wymagane pola body: `category`, `eaten_at`, `source`, `calories`
  - Opcjonalne pola body: `notes`
  - Warunkowe pola body:
    - Dla `source` ∈ {`ai`, `edited`}: wymagane `protein`, `fat`, `carbs`, `analysis_run_id`
    - Dla `source` = `manual`: zabronione `analysis_run_id`, `protein`, `fat`, `carbs`
- Walidacje wejścia:
  - `category` musi istnieć w `meal_categories.code` (case-sensitive match)
  - `eaten_at` w formacie ISO8601, konwersja do `datetime` (UTC-aware)
  - `calories`, `protein`, `fat`, `carbs` jako `Decimal` ≥ 0 z precyzją dwóch miejsc
  - `analysis_run_id` jako UUID v4
  - Limit długości `notes` (np. 1 000 znaków) aby uniknąć nadużyć
- Modele wejściowe:
  - `MealCreatePayload` (Pydantic, warstwa API) z walidatorami kontekstowymi dla pary `source`/makra/analiza
  - `CreateMealCommand` (dataclass/Pydantic) przekazywana do serwisu; zawiera `user_id`, znormalizowane wartości oraz metadane requestu

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `201 Created`
- Nagłówki: `Content-Type: application/json`
- Struktura body:
  - `id`, `user_id`, `category`, `eaten_at`, `source`, `calories`, `protein`, `fat`, `carbs`, `accepted_analysis_run_id`, `created_at`, `updated_at`
  - Konwersja `Decimal` → `float` podczas serializacji
- Modele wyjściowe:
  - `MealResponse` (Pydantic) lub istniejący DTO mapujący encję ORM na JSON
  - Utrzymywać zgodność nazw pól z dokumentacją API (`accepted_analysis_run_id` zamiast `analysis_run_id`)

## 4. Przepływ danych

- Autoryzacja JWT (Supabase) → zależność FastAPI `get_current_user` zwracająca profil z `user_id`.
- FastAPI mapuje payload na `MealCreatePayload`, uruchamia walidatory (np. `root_validator` / `model_validator` Pydantic v2).
- Handler konstruuje `CreateMealCommand` i przekazuje do `MealService.create_meal` wraz sesją bazy danych klienta Supabase.
- `MealService.create_meal`:
  - Weryfikuje `meal_categories` przez zapytanie SELECT.
  - Dla źródeł AI/edited pobiera `analysis_runs` należące do użytkownika, potwierdza status `succeeded`, brak przypisanego `accepted_analysis_run_id`, zgodność `user_id`.
  - Przygotowuje rekord `Meal` ustawiając `accepted_analysis_run_id` przy źródłach AI/edited; dla manual ustawienia makr w `NULL` zgodnie z constraintem.
  - Wykonuje insert w transakcji; w razie potrzeby stosuje `SELECT FOR UPDATE` na `analysis_runs` by uniknąć wyścigów akceptacji.
  - Zwraca encję ORM po commit (z `refresh` jeśli konieczne).
- Handler serializuje wynik do `MealResponse` i zwraca z kodem 201.

## 5. Względy bezpieczeństwa

- Wymóg uwierzytelnienia JWT; brak anonimizowanego dostępu.
- Brak przyjmowania `user_id` w payloadzie; identyfikacja użytkownika tylko z tokena.
- Walidacja własności `analysis_run_id` eliminuje eskalację uprawnień między kontami.
- Parametryzowane zapytania klienta Supabase chronią przed SQLi; limiter długości `notes` redukuje ataki DoS/overflow.
- Supabase RLS: upewnić się, że polityki pozwalają na insert `meals` tylko właścicielowi (`auth.uid()` = `user_id`).
- Rozważyć audit logging (np. middleware) dla operacji tworzenia jeśli wymagane przez compliance.

## 6. Obsługa błędów

- `400 Bad Request`: naruszenie walidacji Pydantic, błędny format czasu, wartości ujemne, niespełnione warunki `source`/makra/analiza.
- `401 Unauthorized`: brak lub przeterminowany token; zwracany przez zależność `get_current_user`.
- `404 Not Found`: brak kategorii w `meal_categories`, brak `analysis_run_id` dla użytkownika lub analiza w innym statusie.
- `409 Conflict`: wskazany `analysis_run_id` już zaakceptowany przez inny posiłek (sprawdzane w serwisie lub poprzez constraint unikalności).
- `500 Internal Server Error`: nieoczekiwane błędy DB/serwisu; logować przez globalny handler. Jeśli dostępna tabela błędów (np. `app_error_logs`), wywołać repozytorium logujące z kontekstem wyjątku i danymi `user_id`, `analysis_run_id`.
- Mapowanie wyjątków domenowych (`CategoryNotFoundError`, `AnalysisRunInvalidError`, ...) na odpowiednie kody w handlerze FastAPI.

## 7. Wydajność

- Korzystać z async klienta Supabase do odpytywania tabel
- Serializację `Decimal` wykonywać w modelach Pydantic (np. korzystając z `field_serializer`) aby uniknąć ręcznego kastowania.

## 8. Kroki implementacji

1. Dodać w `app/api/v1/schemas/meals.py` model `MealCreatePayload` z walidatorami oraz `MealResponse` z serializerami `Decimal`.
2. Rozszerzyć/utworzyć `app/services/meals.py` z metodą `create_meal` implementującą walidacje kategorii, analizy, logikę makr oraz obsługę wyjątków domenowych.
3. Uzupełnić repozytoria w `app/db/repositories/meals.py` o funkcje pomocnicze (`get_category`, `get_analysis_run_for_user`, `mark_analysis_as_accepted`) korzystające z klienta Supabase i zarządzania transakcjami po stronie aplikacji.
4. Dodać endpoint FastAPI w `app/api/v1/endpoints/meals.py`, injekcja `MealService`, `CurrentUser`, klient Supabase; mapowanie wyjątków na odpowiedzi HTTP.
