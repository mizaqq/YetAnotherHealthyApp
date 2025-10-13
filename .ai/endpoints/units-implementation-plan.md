# API Endpoint Implementation Plan: Units

## 1. Przegląd punktu końcowego

- Udostępnić publiczne słowniki jednostek miary z przeliczeniem na gramy dla UI oraz logiki AI.
- Zapewnić drugi endpoint zwracający lokalizowane aliasy danej jednostki, aby interfejs mógł prezentować przyjazne etykiety.
- Oba endpointy są tylko-do-odczytu, wymagają autoryzacji i wykorzystują paginację kursorem zgodnie z politykami Supabase RLS.

## 2. Szczegóły żądania

- Metoda HTTP: `GET`
- Struktury URL:
  - `/api/v1/units`
  - `/api/v1/units/{unit_id}/aliases`
- Parametry `GET /api/v1/units`:
  - Wymagane: brak.
  - Opcjonalne:
    - `unit_type`: string/enum (`mass`, `piece`, `portion`, `utensil`).
    - `search`: string (trimowany, max 100 znaków, case-insensitive LIKE na `code`).
    - `page[size]`: int (domyślnie 50, zakres 1-100).
    - `page[after]`: string (base64 JSON kursora `{"last_id": uuid, "last_code": str}`) dla stabilnego sortowania.
- Parametry `GET /api/v1/units/{unit_id}/aliases`:
  - Path: `unit_id` (UUID).
  - Query: `locale` (opcjonalny, domyślnie `pl-PL`, walidacja regex `^[a-z]{2}-[A-Z]{2}$`).
- Request Body: brak.

## 4. Szczegóły odpowiedzi

- `GET /api/v1/units` → `200 OK`
  - JSON `{ "data": UnitDefinition[], "page": { "size": int, "after": str | null } }`.
- `GET /api/v1/units/{unit_id}/aliases` → `200 OK`
  - JSON `{ "unit_id": uuid, "aliases": UnitAlias[] }`.
- Puste wyniki zwracają `data: []` lub `aliases: []` bez błędu.

## 5. Przepływ danych

- FastAPI endpointy przyjmują zapytania, mapują parametry na DTO i przekazują do `UnitsService` przez DI.
- `UnitsService.list_units` wykonuje zapytanie read-only do Supabase Postgres (`public.unit_definitions`).
  - Filtrowanie po `unit_type` i `search` (ILIKE) wykonywane w warstwie SQL, sortowanie po `code`, `id` dla deterministycznej paginacji.
  - Paginacja: dekodowanie kursora (JSON base64) → wartości `last_code`, `last_id`, użycie warunku `(code, id) > (...)`.
  - Wynik mapowany do DTO + generacja nowego kursora z ostatniego rekordu.
- `UnitsService.get_unit_aliases`:
  - Weryfikuje istnienie rekordu w `public.unit_definitions` (SELECT 1, RLS).
  - Pobiera aliasy z `public.unit_aliases` z opcjonalnym filtrem `locale` lub wszystkimi, sortuje `is_primary DESC`, `alias ASC`.
- Serwis wykorzystuje współdzielony klient Supabase (dependency `get_supabase_client`) operujący na tabelach `public.unit_definitions` i `public.unit_aliases`.
- Odpowiedzi serializowane przez Pydantic i zwracane FastAPI.

## 6. Względy bezpieczeństwa

- Wymaga nagłówka autoryzacji (Supabase JWT) — użyć dependency `get_current_user`.
- Polega na Supabase RLS: zarówno `unit_definitions`, jak i `unit_aliases` muszą posiadać polityki umożliwiające `select` dla roli `authenticated` (sprawdzić, dodać migrację jeśli brak).
- Walidacja wszystkich wejść przez Pydantic; odrzucić nieprawidłowe `unit_type`, `page[size]`, `page[after]`, `locale` `400`.
- Sanitizacja `search`: trim, usunięcie znaków sterujących, limit długości, zablokowanie `%`/\*? — rely on parameterized queries to zapobiec SQL injection.
- Brak danych wrażliwych w odpowiedzi; mimo to logować bez payloadów zawierających tokeny.

## 7. Obsługa błędów

- `400 Bad Request`: nieprawidłowe parametry (walidacja Pydantic lub ręczna validacja kursora).
- `401 Unauthorized`: brak/nieprawidłowy token (obsługiwane przez globalne dependency).
- `404 Not Found`: `unit_id` nie istnieje lub niedostępny przez RLS w alias endpoint.
- `500 Internal Server Error`: błędy DB, problemy z dekodowaniem kursora nieobsłużone, inne wyjątki.
- Logowanie: użyć `structlog` (lub centralnego loggera) z kontekstem (`endpoint`, `user_id`, `params`). W przypadku błędu 500 rozważyć rejestrowanie w `app.services.error_log` jeżeli istnieje integracja; inaczej loga strukturalne + Sentry hooks.

## 8. Rozważania dotyczące wydajności

- Paginate <100 rekordów; używać `LIMIT page_size + 1` dla detekcji dalszych stron i minimalizować transfer danych.
- Reużywać połączeń DB przez DI, operacje read-only bez transakcji wieloetapowych.
- Upewnić się, że serializacja Decimal → string wykonywana w Pydantic `field_serializer` by uniknąć konwersji w pętli.

## 9. Kroki implementacji

2. Utworzyć Pydantic modele w `app/schemas/units.py` (`UnitsListQuery`, `CursorPage`, `UnitDefinition`, `UnitsListResponse`, `UnitAlias`, `UnitAliasesResponse`).
3. Dodać serwis `UnitsService` w `app/services/units_service.py` (metody `list_units`, `get_unit_aliases`) oraz repozytorium Supabase w `app/db/repositories/unit_repository.py` wykorzystujące klienta Supabase.
4. Skonfigurować FastAPI endpoints w `app/api/v1/endpoints/units.py` z routerem, dependency `Depends(UnitsService)`, mapowaniem DTO.
5. Zaimplementować logikę paginacji kursorem (helper w `app/lib/pagination.py` jeżeli istnieje; w przeciwnym razie utworzyć moduł wspólny).
6. Zapewnić obsługę błędów: ValueError z kursora → `HTTPException(status_code=400)`, brak jednostki → `HTTPException(404)`.
