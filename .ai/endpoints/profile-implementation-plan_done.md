# API Endpoint Implementation Plan: POST /api/v1/profile/onboarding

## 1. Przegląd punktu końcowego

- Celem endpointu jest utworzenie lub finalizacja profilu użytkownika w procesie onboardingu na podstawie deklarowanego dziennego celu kalorycznego.
- Operacja jest idempotentna: pierwsze wywołanie tworzy/uzupełnia rekord profilu, kolejne z tą samą logiką zwracają istniejący stan lub zgłaszają konflikt, jeśli onboarding został już zamknięty.
- Endpoint zwraca aktualny stan profilu w formacie zgodnym z `GET /api/v1/profile`.

## 2. Szczegóły żądania

- Metoda HTTP: `POST`
- Struktura URL: `/api/v1/profile/onboarding`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`, `Content-Type: application/json`
- Parametry:
  - Wymagane: brak parametrów ścieżki ani query; kontekst użytkownika pobierany z tokena
  - Opcjonalne: brak
- Request Body (`application/json`):
  - `daily_calorie_goal` – liczba zmiennoprzecinkowa ≥ 0, precyzja do dwóch miejsc po przecinku
- Zastosowane DTO i modele:
  - `ProfileOnboardingRequest` (Pydantic v2) z polem `daily_calorie_goal: condecimal(max_digits=10, decimal_places=2, ge=0)` oraz walidatorem górnego limitu (np. ≤ 10000) i normalizacją do dwóch miejsc
  - Komenda `CompleteOnboardingCommand(user_id: UUID, daily_calorie_goal: Decimal, completed_at: datetime)` przekazywana do serwisu

## 3. Szczegóły odpowiedzi

- Sukces:
  - Kod `201 Created`
  - Nagłówek `Location: /api/v1/profile`
  - Body: profil w formacie `ProfileResponse`
- Scenariusz idempotentny przy istniejącym profilu nieukończonym: nadal `201` z aktualnym profilem
- Błędy:

  - `400 Bad Request` – nieprawidłowa wartość celu kalorycznego
  - `401 Unauthorized` – brak lub nieważny token
  - `409 Conflict` – onboarding już ukończony (`onboarding_completed_at` ≠ NULL)
  - `500 Internal Server Error` – niespodziewane błędy serwera/DB

- DTO wyjściowe: `ProfileResponse`
  - `user_id: UUID4`
  - `daily_calorie_goal: Decimal`
  - `onboarding_completed_at: datetime | None`
  - `created_at: datetime`
  - `updated_at: datetime`

## 4. Przepływ danych

1. FastAPI dependency pozyskuje z nagłówka JWT identyfikator użytkownika (`user_id`) z Supabase (`sub`).
2. Endpoint parsuje i waliduje `ProfileOnboardingRequest` przy użyciu Pydantic.
3. Tworzony jest `CompleteOnboardingCommand` (ustawienie `completed_at` na `datetime.utcnow()`).
4. `ProfileService` sprawdza, czy rekord w `public.profiles` istnieje:
   - Brak rekordu → `INSERT` z danymi (w tym `timezone` default), `onboarding_completed_at` ustawione na `completed_at`.
   - Profil istniejący, `onboarding_completed_at` NULL → aktualizacja `daily_calorie_goal`, `onboarding_completed_at`, `updated_at`.
   - Profil istniejący, `onboarding_completed_at` ustawione → wyjątek konfliktu.
5. Serwis korzysta z warstwy repozytorium (np. `ProfileRepository`) operującej na Supabase Postgres (Supabase client) z klauzulą `RETURNING` i RLS wymuszającym `user_id`.
6. Zwracany profil jest mapowany do `ProfileResponse` i odsyłany przez endpoint.

## 5. Względy bezpieczeństwa

- Autoryzacja: wymagany ważny token Supabase co najmniej roli `authenticated`; brak wejścia użytkownika dla `user_id`.
- Walidacja danych: ograniczenie zakresu `daily_calorie_goal`, ochrona przed wartościami ekstremalnymi i typami niezgodnymi.
- Odporność na race conditions: operacje `INSERT ... ON CONFLICT` lub blokada `SELECT ... FOR UPDATE` w transakcji, aby uniknąć duplikatów.
- Brak ekspozycji danych innych użytkowników – odpowiedź zawiera tylko dane bieżącego profilu.

## 6. Obsługa błędów

- Walidacja wejścia generuje `HTTPException(status_code=400, detail=...)` z czytelnym komunikatem.
- Już ukończony onboarding → `HTTPException(status_code=409, detail="onboarding already completed")`.
- Błędy autoryzacji propagowane z dependency (401).
- Niespodziewane błędy DB: przechwycone i logowane (logger strukturalny), zwracamy `HTTPException(500, detail="internal error")` bez szczegółów DB.
- Brak dedykowanej tabeli błędów – polegamy na centralnym loggerze/observability.

## 7. Rozważania dotyczące wydajności

- Operacja dotyczy pojedynczego wiersza; koszt minimalny.
- Wymagane indeksy: `profiles` ma PK po `user_id`; dodatkowych indeksów brak.
- Skonfigurować retry logic w repozytorium dla chwilowych błędów połączenia.

## 8. Etapy wdrożenia

1. Zidentyfikować istniejące moduły (`app/api/v1/router.py`, `app/services/profile_service.py`, repozytorium) i przygotować dependency na `ProfileService`.
2. Dodać Pydantic modele `ProfileOnboardingRequest`, `ProfileResponse`, `CompleteOnboardingCommand` do `app/schemas/profile.py`.
3. Rozszerzyć/utworzyć `ProfileService.complete_onboarding`, wykorzystując transakcję oraz obsługę trzech scenariuszy (brak profilu, w trakcie onboarding, zakończony).
4. W repozytorium dodać metody `get_profile_for_update(user_id)`, `upsert_profile(...)` z SQL wspierającym `RETURNING`.
5. Zaimplementować endpoint w `app/api/v1/router.py` jako async handler korzystający z dependency: `@router.post(..., status_code=201)`.
