### Plan testów jednostkowych — backend

#### Cel

- Zwiększyć pewność zmian w logice biznesowej i bezpieczeństwie autoryzacji.
- Szybko wykrywać regresje w operacjach na danych i paginacji.

#### Zakres (unit)

- Warstwa services: logika biznesowa, transformacje, mapowanie błędów.
- Schematy (Pydantic) i funkcje pomocnicze: walidacja, kursory, paginacja.
- Krytyczne zależności `core/dependencies` (autoryzacja) — bez realnego I/O.

Poza zakresem (lepsze w integracyjnych):

- Endpointy FastAPI i routing, realny HTTP/IO (`OpenRouterClient`, Supabase).

#### Konwencje i narzędzia

- `pytest`, `pytest-asyncio` (testy async), `pytest-mock`/`unittest.mock` (mocki), opcjonalnie `freezegun` (czas).
- Nazewnictwo: `test_<moduł>__<scenariusz>__<oczekiwanie>()`.
- Każdy test: ścieżka sukcesu i co najmniej jedna ścieżka błędu.

#### Struktura plików testów

- `apps/backend/tests/unit/services/`
  - `test_meal_service.py`
  - `test_analysis_runs_service.py`
  - `test_reports_service.py`
  - `test_openrouter_service.py`
  - (opcjonalnie) `test_product_service.py`, `test_units_service.py`, `test_profile_service.py`, `test_meal_categories_service.py`
- `apps/backend/tests/unit/core/`
  - `test_dependencies_auth.py` (dla `get_current_user_id`)
- `apps/backend/tests/unit/api_schemas/`
  - `test_meals_schema_and_cursors.py`
  - `test_pagination_pageinfo.py`
- `apps/backend/tests/unit/db/` (tylko transformacje, gdy występują)
  - `test_*_repository.py`

#### Priorytety (od najwyższego)

1. `app/services/meal_service.py`
2. `app/services/analysis_runs_service.py` + `app/services/analysis_processor.py`
3. `app/services/reports_service.py`
4. `app/services/openrouter_service.py`
5. `app/core/dependencies.py:get_current_user_id`
6. `app/api/v1/schemas/meals.py` (walidacja zapytań, `encode_*`/`decode_*`)
7. `app/api/v1/pagination.py` (`PageInfo` i spójność)
8. Pozostałe services (jeśli zawierają logikę, nie tylko delegację)

#### Scenariusze testowe (skrót)

- MealService

  - list_meals: bez filtrów (domyślne sortowanie), z filtrami (`from`, `to`, `category`, `source`), `include_deleted`.
  - paginacja: poprawne `PageInfo`, `next`/`prev` kursory; brak `next` przy końcu; solidność `encode/decode`.
  - błędy repo (np. wyjątek) → mapowanie na `HTTPException` z właściwym statusem.
  - (jeśli dostępne) create/update/delete: walidacja danych, mapowanie błędów.

- AnalysisRunsService + analysis_processor

  - start/run flow: poprawne wywołania repo (kolejność), zapis elementów analizy.
  - odpowiedzi z `OpenRouterService`: poprawne parsowanie i przypisanie; częściowe błędy (niektóre elementy nie parsują się).
  - propagacja wyjątków i metadanych (np. statusy, licznik błędów).

- ReportsService

  - agregacje dzienne/tygodniowe/miesięczne: poprawne sumy i makra; puste zakresy.
  - krawędzie czasu (początek/koniec dnia), strefy czasowe — testy z zamrożonym czasem.

- OpenRouterService

  - walidacja i interpretacja odpowiedzi AI (poprawna, niekompletna, błędna struktura JSON).
  - dopasowanie produktów (brak dopasowania, wiele dopasowań, dopasowanie jednoznaczne).
  - limity/dedykowane błędy API (mapowanie na kontrolowane wyjątki/rezultaty).

- core/dependencies.get_current_user_id

  - brak nagłówka → 401, poprawne `WWW-Authenticate`.
  - zły format (nie `Bearer <token>`) → 401 z komunikatem.
  - token niepoprawny/wygasły → 401.
  - token poprawny → zwraca `UUID` użytkownika.
  - błąd klienta Supabase → 401 i logowanie błędu.

- api/v1/schemas/meals.py

  - `MealListQuery`: poprawne domyślne wartości, walidacja `page[size]`, `sort`.
  - `MealSource` (enum): serializacja/deserializacja, niepoprawne wartości.
  - kursory: `encode_meal_cursor`/`decode_meal_cursor` — symetria, nieprawidłowe wejścia.

- pagination.PageInfo

  - spójność pól (`has_next`/`has_prev` vs obecność cursorów), wartości skrajne.

- Repositories (opcjonalnie)
  - tylko transformacje danych/rekordów → modele; bez realnych zapytań.

#### Strategie mockowania

- Repozytoria: fake/stub klasy z oczekiwanymi zwrotkami; symulacja wyjątków.
- `get_supabase_client` i `OpenRouterClient`: patch przez `mocker.patch`/`monkeypatch` na test doubles.
- Czas: `freezegun.freeze_time` dla testów raportów i sortowania/kursorów.
- wszystkie zewnetrzne serwisy powinny być mockowane

#### Fixtury (propozycje)

- `user_id` (UUID), `now` (zamrożony czas), dane przykładowych posiłków/raportów.
- Stub repo: `meal_repository_stub`, `product_repository_stub`, `reports_repository_stub`.
- Stub `openrouter_response_valid/invalid`.

#### Kryteria jakości

- Pokrycie: min. 85% w `app/services`, 100% dla funkcji kursorów i `get_current_user_id`.
- Każdy test weryfikuje zarówno wynik, jak i interakcje (liczba wywołań repo/klienta, parametry).

#### Uruchamianie

- Z katalogu `apps/backend`: `pytest -q` lub z raportem: `pytest -q --maxfail=1 -x`.

#### Dodatkowe uwagi

- Dodając nowe endpointy lub reguły walidacji, najpierw dopisz testy services/schematów.
- Błędy produkcyjne powinny skutkować dodaniem testu regresyjnego w odpowiednim module.
