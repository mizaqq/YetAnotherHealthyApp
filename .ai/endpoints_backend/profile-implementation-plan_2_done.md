# API Endpoint Implementation Plan: PATCH /api/v1/profile

## 1. Przegląd punktu końcowego

- Endpoint aktualizuje wybrane pola profilu użytkownika (obecnie dzienny cel kaloryczny i ewentualne oznaczenie ukończenia onboardingu).
- Pozwala użytkownikowi zmienić swoje cele żywieniowe lub ponownie oznaczyć status onboardingu.
- Zwraca zaktualizowany profil w formacie spójnym z pozostałymi endpointami profilu.

## 2. Szczegóły żądania

- Metoda HTTP: `PATCH`
- Struktura URL: `/api/v1/profile`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Content-Type: application/json`
- Parametry:
  - Wymagane: brak parametrów ścieżki/query; `user_id` pochodzi z tokena
  - Opcjonalne: brak
- Request Body (`application/json` – pola opcjonalne):
  - `daily_calorie_goal` – Decimal ≥ 0, dokładność 2 miejsca po przecinku (opcjonalne)
  - `onboarding_completed_at` – `datetime` lub `null`; `null` pozwala cofnąć status
- Wykorzystane DTO/Modele:
  - `ProfileUpdateRequest`: oba pola opcjonalne, walidacja współzależności
  - Komenda `UpdateProfileCommand(user_id: UUID, daily_calorie_goal: Decimal | None, onboarding_completed_at: datetime | None)`

## 3. Szczegóły odpowiedzi

- Sukces:
  - Kod `200 OK`
  - Body: zaktualizowany `ProfileResponse`
- Błędy:
  - `400 Bad Request` – gdy żadne pole nie zostało przekazane, pole spoza domeny lub przekroczono dozwolone limity
  - `401 Unauthorized` – brak/wadliwy token
  - `404 Not Found` – profil nie istnieje (brak wcześniejszego onboardingu)
  - `500 Internal Server Error` – nieoczekiwane problemy

## 4. Przepływ danych

1. Dependency FastAPI uwierzytelnia użytkownika i wyciąga `user_id`.
2. Endpoint waliduje `ProfileUpdateRequest`, sprawdzając co najmniej jedno pole do aktualizacji.
3. Tworzony jest `UpdateProfileCommand` z przekazanymi wartościami.
4. `ProfileService` korzysta z repozytorium:
   - Pobiera rekord (np. `SELECT ... FOR UPDATE`), aby zapewnić spójność.
   - Aktualizuje tylko przekazane pola; niezmienione pozostają bez zmian.
   - Ustawia `updated_at = now()` i w razie potrzeby normalizuje `daily_calorie_goal` do dwóch miejsc.
5. Zaktualizowany rekord mapowany jest do `ProfileResponse` i zwracany.

## 5. Względy bezpieczeństwa

- Autoryzacja Supabase JWT jak w pozostałych endpointach.
- RLS musi zezwalać na `UPDATE` tylko właścicielowi (`uid() = user_id`).
- Walidacja business rules: blokada wartości ujemnych, górny limit (np. ≤ 10000 kcal), spójność dat (przyszłość dozwolona?).
- Zachować idempotencję – wielokrotne wywołanie z tymi samymi danymi nie zmienia stanu.

## 6. Obsługa błędów

- Brak pól do aktualizacji → `HTTPException(400, detail="payload empty")`.
- Ujemny cel kaloryczny → `HTTPException(400, detail="invalid daily_calorie_goal")`.
- Brak profilu → `HTTPException(404, detail="profile not found")`.
- Błędy DB → logowanie i `HTTPException(500, detail="internal error")`.
- Logować istotne zdarzenia (INFO – aktualizacja profilu, WARN – próba aktualizacji nieistniejącego profilu).

## 7. Rozważania dotyczące wydajności

- Aktualizacja pojedynczego wiersza; wpływ marginalny.
- Warto zadbać o optymalne zarządzanie transakcją (krótka sekcja krytyczna) i użycie RLS.
- Można rozważyć `UPDATE ... WHERE user_id = :id RETURNING *` dla jednego roundtripu.

## 8. Etapy wdrożenia

1. Dodać `ProfileUpdateRequest` do `app/schemas/profile.py` z walidatorami (co najmniej jedno pole, zakres celu kalorycznego, poprawność daty).
2. Utworzyć klasę `UpdateProfileCommand` i metodę `ProfileService.update_profile(command)` obsługującą transakcję i warunki brzegowe.
3. Rozszerzyć repozytorium o funkcję `update_profile(user_id, data)` zwracającą pełny rekord.
4. Dodać endpoint w `app/api/v1/router.py`: `@router.patch("/profile", response_model=ProfileResponse)`.
5. Mapować wyjątki `ProfileNotFoundError`, `InvalidProfileUpdateError` na `HTTPException(404/400)`.
6. Przygotować testy jednostkowe serwisu i repozytorium (scenariusze: sukces, brak profilu, weryfikacja walidacji) oraz testy integracyjne endpointu.
7. Upewnić się, że polityki RLS umożliwiają `UPDATE` tylko właścicielowi; w razie potrzeby przygotować migrację.
8. Zaktualizować dokumentację OpenAPI/README.
