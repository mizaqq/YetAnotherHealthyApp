# API Endpoint Implementation Plan: GET /api/v1/profile

## 1. Przegląd punktu końcowego

- Endpoint zwraca aktualny profil zalogowanego użytkownika, w tym dzienny cel kaloryczny i status onboardingu.
- Wspiera klienta w prezentowaniu pulpitu użytkownika oraz sprawdzaniu, czy onboarding został ukończony.
- Nie tworzy ani nie aktualizuje danych; jedynie odczytuje rekord z `public.profiles`.

## 2. Szczegóły żądania

- Metoda HTTP: `GET`
- Struktura URL: `/api/v1/profile`
- Nagłówki: `Authorization: Bearer <Supabase JWT>`
- Parametry:
  - Wymagane: brak parametrów ścieżki lub query; kontekst użytkownika pochodzi z tokena
  - Opcjonalne: brak
- Request Body: brak
- Wykorzystane DTO/Modele:
  - Zapytanie: `GetProfileQuery(user_id: UUID)` przekazywane do serwisu
  - Odpowiedź: `ProfileResponse` (współdzielona z endpointami POST/PATCH)

## 3. Szczegóły odpowiedzi

- Sukces:
  - Kod `200 OK`
  - Body (`ProfileResponse`): `user_id`, `daily_calorie_goal`, `onboarding_completed_at`, `created_at`, `updated_at`
- Błędy:
  - `401 Unauthorized` – brak lub niepoprawny token
  - `404 Not Found` – profil nie istnieje
  - `500 Internal Server Error` – nieoczekiwane problemy po stronie serwera/DB

## 4. Przepływ danych

1. Middleware/dependency uwierzytelnia żądanie i wyciąga `user_id` z Supabase JWT (`sub`).
2. Endpoint buduje `GetProfileQuery` i deleguje do `ProfileService`.
3. `ProfileService` korzysta z repozytorium (`ProfileRepository`) do pobrania rekordu z `public.profiles` (SELECT z RLS).
4. Jeśli rekord nie istnieje, serwis zgłasza wyjątek domenowy mapowany na `404`.
5. Istniejący rekord jest mapowany do `ProfileResponse` i zwracany klientowi.

## 5. Względy bezpieczeństwa

- Wymagane uwierzytelnienie Supabase (`authenticated` rola minimalna).
- Zastosowane polityki RLS muszą ograniczać SELECT do `user_id` zgodnego z `auth.uid()`.
- Brak danych wrażliwych innych użytkowników; zwracamy tylko dane bieżącego profilu.
- Weryfikacja, że endpoint nie ujawnia, czy profil nie istnieje użytkownikowi niezalogowanemu (401 priorytet nad 404 dla braku autoryzacji).

## 6. Obsługa błędów

- Brak tokena lub nieważny → `HTTPException(401, detail="unauthorized")`.
- Brak rekordu → `HTTPException(404, detail="profile not found")`.
- Problemy DB (timeout, błąd połączenia) → logowanie na poziomie ERROR i `HTTPException(500, detail="internal error")`.
- Wykorzystać centralny logger (np. `structlog`) z kontekstem `user_id` i `endpoint`.

## 7. Rozważania dotyczące wydajności

- Operacja pojedynczego SELECT-a po kluczu głównym (`user_id`); minimalne obciążenie.
- Upewnić się, że połączenia DB są ponownie wykorzystywane przez async session (pooling).
- Obsłużyć ewentualne warm cache (np. FastAPI dependency caching) jeśli w przyszłości profil będzie często pobierany.

## 8. Etapy wdrożenia

1. Dodaj `GetProfileQuery` do warstwy serwisu lub repozytorium.
2. Rozszerz `ProfileService` o metodę `get_profile(user_id: UUID) -> Profile` z obsługą wyjątku `ProfileNotFoundError`.
3. Zaimplementuj metodę repozytorium `fetch_profile(user_id: UUID)` wykonującą `SELECT` z `RETURNING` lub zwykłym fetch; uwzględnij RLS.
4. Utwórz handler FastAPI w `app/api/v1/router.py`: `@router.get("/profile", response_model=ProfileResponse)`.
5. Zamapuj wyjątki domenowe na `HTTPException` (404) w warstwie endpointu lub globalnym handlerze.
6. Dodaj testy jednostkowe serwisu (scenariusze: profil istnieje/nie istnieje) oraz testy integracyjne endpointu obejmujące 200, 401, 404.
7. Zaktualizuj dokumentację OpenAPI/README i plan wdrożenia.
