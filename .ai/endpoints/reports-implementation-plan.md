# API Endpoint Implementation Plan: GET `/api/v1/reports/daily-summary`

## 1. Przegląd punktu końcowego

- Dostarcza zagregowane wartości kalorii i makroskładników dla konkretnego dnia użytkownika, bazując na zapisanych posiłkach w `public.meals` i powiązanych analizach.
- Wykorzystuje profil użytkownika (`public.profiles`) do ustalenia strefy czasowej oraz dziennego celu kalorycznego, aby zwrócić metrykę progresu.
- Zapewnia listę posiłków (ID, kategoria, kalorie, `eaten_at`) uporządkowaną chronologicznie dla wskazanego dnia.

## 2. Szczegóły żądania

- Metoda HTTP: `GET`
- Struktura URL: `/api/v1/reports/daily-summary`
- Parametry zapytania:
  - Wymagane: brak (endpoint domyślnie używa „dzisiaj” w strefie użytkownika).
  - Opcjonalne:
    - `date` (`str`, ISO 8601 `YYYY-MM-DD`): dzień raportu liczony w strefie czasowej profilu.
- Nagłówki: `Authorization: Bearer <Supabase JWT>` (obsługiwany przez globalny dependency auth).
- Walidacja wejścia:
  - Pydantic query model `DailySummaryQuery` z walidatorem parsującym datę (obsługa błędnych formatów → 400).
  - Limitowanie zakresu (np. 365 dni wstecz/przód) oraz blokowanie dat sprzed utworzenia profilu.
  - Normalizacja daty na `datetime` w strefie profilu (wykorzystuje `profile.timezone`).

## 3. Szczegóły odpowiedzi

- Kod sukcesu: `200 OK`.
- Schemat odpowiedzi (`DailySummaryResponse` Pydantic):
  - `date` (`date`): dzień raportu.
  - `calorie_goal` (`Decimal | None`): dzienny cel z profilu (opcjonalny, gdy brak wpisu).
  - `totals` (`DailySummaryTotals`): `calories`, `protein`, `fat`, `carbs` jako `Decimal`, z `0` gdy brak danych (z `COALESCE`).
  - `progress` (`DailySummaryProgress`): `calories_percentage` (`Decimal`) wyliczany z ochroną przed dzieleniem przez zero.
  - `meals` (`List[DailySummaryMeal]`): każdy element zawiera `id`, `category`, `calories`, `eaten_at` (ISO 8601 z offsetem).
- Odpowiedź JSON w pełni zgodna ze specyfikacją API; formaty pól numerycznych ustawione przez `Config` (`json_encoders` dla `Decimal`).

## 4. Przepływ danych

- Autoryzacja: dependency pobiera `user_id` z tokena Supabase i udostępnia go endpointowi.
- Profil: zapytanie do `public.profiles` po `user_id` (SELECT `daily_calorie_goal`, `timezone`).
- Zakres czasowy:
  - Obliczenie `start_ts` i `end_ts` w UTC na podstawie `date` i `profile.timezone` (`pytz` / `zoneinfo`).
  - Wykorzystanie tych granic w zapytaniu do `public.meals` z RLS (automatycznie ogranicza do `user_id`).
- Agregacja posiłków:
  - Jedno zapytanie `SELECT SUM(...)` z `COALESCE` + konwersja `NUMERIC` → `Decimal`.
  - Osobne zapytanie (lub CTE w jednym) pobierające listę posiłków dla dnia, filtruje `deleted_at IS NULL`, sortuje po `eaten_at` asc.
  - Uwzględnienie posiłków `source='manual'` (makra NULL → 0) przy agregacji.
- Obliczanie progresu: po stronie serwisu (Python) wylicza procent celu z zaokrągleniem (`quantize` / `round`) do np. 1 miejsca.
- Złożenie obiektu odpowiedzi w serwisie (`ReportsService`) i zwrócenie poprzez endpoint.

## 5. Względy bezpieczeństwa

- Wymagana autentykacja Supabase JWT; brak tokena lub token niepoprawny → `401` (obsługiwane przez dependency).
- RLS na `public.profiles` i `public.meals` wymusza `user_id = auth.uid()`, co izoluje dane.
- Walidacja parametru `date` zabezpiecza przed SQL injection (użycie parametrów bindowanych).
- Ograniczenie zakresu dat i brak surowych danych modelu; ujawniamy wyłącznie dane użytkownika.
- Opcjonalne rate limiting na poziomie middleware (np. 120 req/min / user) dla endpointów raportowych.

## 6. Obsługa błędów

- `400 Bad Request`: nieprawidłowy format `date`, data poza dozwolonym zakresem, data przed stworzeniem profilu.
- `401 Unauthorized`: brak / wygasły / błędny token.
- `404 Not Found`: brak rekordu profilu (niespójna baza) – zwrócić 404 zamiast pustego wyniku.
- `500 Internal Server Error`: nieoczekiwane wyjątki (np. błąd połączenia z DB). Logować poprzez `structlog` + Sentry, maskować szczegóły w odpowiedzi.
- Rejestrowanie błędów: użyć istniejącego loggera aplikacji; jeżeli globalna obsługa błędów zapisuje do dedykowanej tabeli/error tracker, przekazać kontekst (`endpoint`, `user_id`, `query_params`).

## 7. Wydajność

- Zapytania ograniczone do jednego dnia z użyciem indeksu `meals_user_id_eaten_at_idx` (filtr `user_id` + `eaten_at`).
- Preferowane pojedyncze zapytanie z CTE (agregaty + lista posiłków) lub dwa lekkie zapytania wykonywane współbieżnie (`asyncio.gather`).
- Minimalizacja transferu – wybieramy tylko potrzebne kolumny (`SELECT id, category, calories, eaten_at`).
- Cache krótkoterminowy (np. in-memory na poziomie serwisu) możliwy dla powtarzanych zapytań tego samego dnia, ale nie obowiązkowy na MVP.

## 8. Kroki implementacji

1. Utworzyć moduł schematów w `app/api/v1/schemas/reports.py` z modelami `DailySummaryQuery`, `DailySummaryResponse` i pomocniczymi DTO (`Totals`, `Progress`, `Meal`).
2. Dodać serwis `ReportsService` w `app/services/reports.py`, implementujący metodę `get_daily_summary(user_id, target_date)` z logiką walidacji zakresu dat, obliczeń i agregacji.
3. Rozszerzyć warstwę dostępu do danych (np. `app/db/reports.py`) o funkcje wykonujące parametryzowane zapytania SQL (async, poprzez istniejący pool / Supabase client).
4. Dodać endpoint `app/api/v1/endpoints/reports.py` z funkcją FastAPI obsługującą trasę, korzystającą z dependency auth i nowego serwisu.
5. Zarejestrować router raportów w `app/api/v1/router.py` pod prefiksem `/reports`.
6. Uwzględnić serializację `Decimal` w globalnej konfiguracji (jeśli nie istnieje) lub w modelach odpowiedzi.
