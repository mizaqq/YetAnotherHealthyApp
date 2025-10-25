<plan_testów>

### 1. Wprowadzenie i cele testowania

- **Cel ogólny**: Zapewnienie wysokiej jakości YetAnotherHealthyApp – aplikacji do szybkiego zapisywania posiłków i monitorowania kalorii/makroskładników – poprzez weryfikację poprawności funkcjonalnej, niezawodności, bezpieczeństwa, dostępności i wydajności na frontendzie (React 19) i backendzie (FastAPI 0.119.0).
- **Cele szczegółowe**:
  - Zweryfikować kluczowe ścieżki użytkownika: rejestracja, reset hasła, onboarding, dodawanie posiłków (w tym analiza AI), przegląd historii, dashboard, profil.
  - Zapewnić spójność kontraktów API (OpenAPI) z klientami przeglądarkowymi (`src/lib/api.ts`) oraz stabilność integracji z Supabase Auth i OpenRouter.
  - Zapewnić podstawowe budżety wydajnościowe (TTI, p95 latencji endpointów krytycznych), podstawowe bezpieczeństwo (autoryzacja, brak enumeracji maili, poprawne kody HTTP) i zgodność z A11y (axe).
  - Ustalić regresję automatyczną obejmującą funkcje krytyczne i paginację.

### 2. Zakres testów

- **Frontend (apps/frontend)**:
  - Warstwa UI/UX: komponenty w `src/components/**` (auth, add-meal, dashboard, history, meal-details, profile, navigation, onboarding).
  - Logika kliencka: hooki w `src/hooks/**`, klient API `src/lib/api.ts`, kontekst odświeżania dashboardu.
  - Integracje: Supabase (sesje/tokeny), wyświetlanie błędów API, paginacja historii (infinite scroll).
- **Backend (apps/backend)**:
  - Endpointy REST w `app/api/v1/**`: `auth`, `profile`, `analysis-runs`, `meals`, `reports`, `meal-categories`, `units`, `products`, `health`.
  - Serwisy domenowe `app/services/**`: m.in. `openrouter_service.py`, `analysis_processor.py`, `meal_service.py`, `reports_service.py`.
  - Konfiguracja i zależności: `app/core/config.py` (OpenRouter, Supabase), `app/core/dependencies.py`, inicjalizacja w `app/main.py`.
  - Warstwa danych: sesja DB (`app/db/session.py`, SQLite), repozytoria `app/db/repositories/**` (jeśli obecne).
- **Integracje zewnętrzne**:
  - Supabase Auth: rejestracja, reset hasła, weryfikacja tokenów.
  - OpenRouter: analiza tekstu posiłku (należy mockować w testach).
- **Poza zakresem (na teraz)**:
  - Pełne testy migracji i danych na produkcyjnej bazie Postgres (repo zawiera migracje Supabase dla danych produktowych, ale backend de facto używa SQLite w dev/testach).
  - Testy UI na wielu urządzeniach realnych (poza najpopularniejszymi rozdzielczościami w E2E).

### 3. Typy testów do przeprowadzenia

- **Analiza statyczna i formatowanie**:
  - Frontend: ESLint, TypeScript type-check.
  - Backend: Ruff (wg `pyproject.toml`), opcjonalnie mypy (gdy zostanie dodany).
- **Testy jednostkowe**:
  - Frontend: Vitest + React Testing Library (komponenty, hooki, logika formatowania/obliczeń).
  - Backend: pytest (serwisy z `app/services/**`, walidacja schematów Pydantic).
- **Testy kontraktowe API**:
  - Schemathesis/Dredd na `/api/v1/openapi.json` (spójność kodów, schematów i odpowiedzi).
  - Zgodność typów DTO w `src/types.ts` z OpenAPI (generacja lub ręczna walidacja krytycznych ścieżek).
- **Testy integracyjne backendu**:
  - FastAPI TestClient/httpx z izolowaną bazą SQLite (pliki tymczasowe), mock Supabase i OpenRouter.
  - Scenariusze łączące endpointy: `analysis-runs` → `meals` → `reports`.
- **Testy integracyjne frontend–backend**:
  - MSW (mock backend) do odtwarzania kodów 401/404/409 i błędów serwera; test zachowania klientów i UI.
- **Testy E2E (Playwright)**:
  - Krytyczne ścieżki: rejestracja, reset hasła, onboarding, dodawanie posiłku z analizą, historia (infinite scroll), dashboard, profil.
- **Testy wydajnościowe**:
  - k6/Gatling: p95 latencja dla `health`, `meal-categories`, `reports/*`, `meals` list.
- **Testy bezpieczeństwa (podstawowe)**:
  - Autoryzacja, poprawne kody błędów, brak ujawniania informacji, brak enumeracji maili (202).
- **Testy dostępności (A11y)**:
  - axe-core w E2E i/lub testy komponentów.

### 4. Scenariusze testowe dla kluczowych funkcjonalności

- **Autoryzacja i konta (Supabase)**:
  - Rejestracja: `POST /api/v1/auth/register`
    - Sukces (201, neutralny komunikat), konflikt (409) dla istniejącego maila, 400 dla złego formatu, 500 fallback.
  - Reset hasła – żądanie: `POST /api/v1/auth/password/reset-request`
    - Zawsze 202 i neutralny komunikat (brak enumeracji), log warning przy błędzie.
  - Reset hasła – potwierdzenie: `POST /api/v1/auth/password/reset-confirm`
    - 204 na sukces z ważnym tokenem, 401 przy nieważnym/wygaśniętym, 400 dla złego formatu hasła, 500 fallback.
  - Brak tokenu w requestach uwierzytelnionych → 401.
- **Onboarding i profil**:
  - `POST /api/v1/profile/onboarding` ustawia `daily_calorie_goal`; `GET/PATCH /api/v1/profile` odczyt/aktualizacja.
  - Walidacja zakresów wartości, 404 gdy profil nie istnieje i wymagany jest onboarding, 401 bez tokenu.
- **Kategorie, jednostki i produkty**:
  - `GET /api/v1/meal-categories?locale=pl` zwraca dane w `data[]`, 200; błędny `locale` (fallback/spójny błąd).
  - `GET /api/v1/units`, `GET /api/v1/products` (jeśli dostępne): paginacja/filtry, 200/404.
- **Analiza posiłku (OpenRouter, AI)**:
  - `POST /api/v1/analysis-runs` tworzy analizę dla tekstu (parametr `threshold` opcjonalny).
  - `GET /api/v1/analysis-runs/{id}/items` zwraca składniki; `POST /{id}/retry` powtarza z innymi parametrami; `POST /{id}/cancel`.
  - Błędy integracji OpenRouter → 502/500 z re-try w serwisie (sprawdzić `max_retries` i backoff z configu).
  - Determinizm testów: dla testów mock odpowiedzi modelu, testy bez-dependency od losowości.
- **Posiłki i historia**:
  - `POST /api/v1/meals` tworzy posiłek z elementami analizy (suma makro, przypisanie do kategorii).
  - `GET /api/v1/meals?{page[size],page[after]}` paginacja; poprawny `nextCursor` w odpowiedzi.
  - `GET /api/v1/meals/{id}?include_analysis_items=true` zwraca detale; `DELETE /{id}` miękkie usunięcie.
  - Infinite scroll (frontend): ładowanie kolejnych stron, obsługa końca danych i błędów sieci.
- **Raporty i dashboard**:
  - `GET /api/v1/reports/daily-summary?date=YYYY-MM-DD` wylicza agregaty vs cel (`daily_calorie_goal`).
  - `GET /api/v1/reports/weekly-trend?end_date=YYYY-MM-DD&include_macros=true` zwraca trend 7‑dniowy.
  - Puste dane vs pełne dane, stabilność formatów, efekty w UI (wykresy, skeletony, stany puste).
- **Health-check**:
  - `GET /api/v1/health` → `{status:"ok"}`, ≤ 100ms p95 lokalnie (baseline dla monitoringu).
- **Zachowanie błędów**:
  - 401 (brak/nieprawidłowy token), 404 (brak zasobu, np. nieistniejący `mealId`), 409 (konflikt), 500 (awarie).
  - Frontend: spójne komunikaty z `handleApiError` (Unauthorized, Resource not found, Conflict, API error).

### 5. Środowisko testowe

- **Lokalne (dev/test)**:
  - Node 20+, pnpm/npm; Python 3.13; Vite dev server; FastAPI (uvicorn).
  - Backend: SQLite test DB (plik tymczasowy) i TestClient/httpx.
  - Zmienne środowiskowe (mock/stub): `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENROUTER_API_KEY` (w testach zastąpione stubami).
- **Izolacja i deterministyczność**:
  - Mock Supabase w zależności `get_supabase_dependency` (zwracaj stub `Client`).
  - Mock OpenRouter w warstwie serwisu/klienta (`openrouter_service.py` / `openrouter_client.py`) – stałe odpowiedzi.
  - Seed danych słownikowych (kategorie, jednostki) dla testów integracyjnych i E2E.
- **Dostęp E2E**:
  - Playwright przeciwko lokalnemu zestawowi (Vite + uvicorn) z MSW do kontrolowania wariantów błędów.

### 6. Narzędzia do testowania

- **Frontend**:
  - Vitest, React Testing Library, MSW (mock API), Playwright (E2E), axe-core (A11y), ESLint, TypeScript.
- **Backend**:
  - pytest, fastapi TestClient/httpx, respx/pytest-httpx (mock zewnętrznych HTTP), Schemathesis (OpenAPI), Ruff, pytest-cov.
- **Wydajność i jakość**:
  - k6 (testy obciążeniowe), Lighthouse (podgląd TTI/FCP w dev), Coveralls/Codecov (raportowanie pokrycia).
- **CI/CD (GitHub Actions)**:
  - Macierz: frontend lint+unit, backend lint+unit+integracyjne, kontraktowe, E2E (na PR krytycznych zmianach).

### 7. Harmonogram testów

- **Tydzień 1**:
  - Skonfigurowanie podstaw toolingu (Vitest/RTL/MSW, pytest/TestClient, Ruff/ESLint).
  - Testy jednostkowe: `src/lib/api.ts` (front) i serwisy `app/services/**` (back).
  - Pierwszy zestaw kontraktów (Schemathesis) dla `health`, `profile`, `meal-categories`.
- **Tydzień 2**:
  - Testy integracyjne backendu: `analysis-runs` → `meals` → `reports`, paginacja `meals`.
  - E2E: rejestracja, reset hasła, onboarding, dashboard, historia (infinite scroll), posiłek end‑to‑end.
  - A11y (axe) dla widoków krytycznych.
- **Tydzień 3**:
  - Wydajność (k6) i twarde budżety; twarde progi pokrycia.
  - Hardening bezpieczeństwa (kody błędów, nagłówki, brak wycieków informacji).
  - Stabilizacja i regresja automatyczna na krytyczne ścieżki.

### 8. Kryteria akceptacji testów

- **Funkcjonalne**:
  - 100% przejść E2E dla: rejestracja, reset hasła (obie fazy), onboarding, dodanie posiłku (z analizą), dashboard, historia, profil.
  - Kontrakt OpenAPI zgodny na 100% dla ścieżek krytycznych (brak rozbieżności schematów/kodów).
- **Jakość kodu i pokrycie**:
  - Pokrycie: backend ≥ 80% (lin./branch), frontend ≥ 70% (lin.), krytyczne moduły ≥ 85%.
  - Brak błędów blokujących w ESLint/Ruff; typu „warning” akceptowane tylko z uzasadnieniem.
- **Wydajność**:
  - p95 latencja lokalnie: `GET /health` ≤ 100ms; `GET /meal-categories`, `GET /reports/*`, `GET /meals` ≤ 300ms; operacje zapisu ≤ 500ms (zależnie od mocków).
- **Bezpieczeństwo**:
  - Brak enumeracji maili (202 dla reset-request zawsze).
  - 401 dla braku/nieprawidłowego tokenu; 404/409 zgodnie z opisem; brak wycieków szczegółów błędów do UI.
- **Dostępność**:
  - Brak poważnych błędów axe (severity „serious/critical”) na głównych widokach.

### 9. Role i odpowiedzialności

- **QA**: projekt i utrzymanie testów E2E/kontraktowych, weryfikacja kryteriów akceptacji, raportowanie defektów.
- **Developerzy FE/BE**: testy jednostkowe/integracyjne własnych modułów, szybka reakcja na regresje, utrzymanie zgodności kontraktów.
- **DevOps/CI**: pipeline (matryca jobów, cache), artefakty testowe (raporty, coverage), tajemnice środowiskowe.
- **PM/Tech Lead**: priorytetyzacja defektów, decyzje o dopuszczeniu do release.

### 10. Procedury raportowania błędów

- **Kanał i format**: GitHub Issues (szablon błędu z polami: środowisko, kroki odtworzenia, oczekiwany vs. rzeczywisty rezultat, logi/konsola, zrzuty ekranu/har).
- **Klasyfikacja ważności**:
  - P0: blokuje krytyczne ścieżki (np. brak możliwości dodania posiłku) – naprawa natychmiast.
  - P1: duże utrudnienie (np. błędne sumy makro) – do 24–48h.
  - P2: mniejsze problemy (UI, edge cases) – kolejne sprinty.
  - P3: drobne usprawnienia/tech debt – planowane.
- **Triage i SLA**:
  - Triage codziennie; przypisanie do właściciela modułu w 24h.
  - Link do PR i testów automatycznych w zgłoszeniu naprawczym.
- **Weryfikacja naprawy**:
  - Re-test manualny/E2E, dodanie testu regresyjnego.
  - Zamknięcie po potwierdzeniu na środowisku docelowym.

### Załączniki operacyjne (skrót)

- **Uruchamianie testów (przykładowo)**:

```bash
# Frontend
cd apps/frontend
npm ci
npm run lint
npm run typecheck
npm run test
# E2E (po uruchomieniu FE i BE)
npx playwright test

# Backend
cd apps/backend
uv run ruff check .
uv run pytest --maxfail=1 --cov=app --cov-report=term-missing

# Kontraktowe (Schemathesis; BE musi wystawiać /openapi.json)
schemathesis run http://localhost:8000/api/v1/openapi.json
```

- **Zasady mockowania**:
  - Frontend: MSW dla scenariuszy 401/404/409/500 i wariantów paginacji.
  - Backend: stub `get_supabase_dependency`, mock OpenRouter w warstwie serwisu/klienta.
- **Dane testowe**:
  - Seed kategorii/jednostek; przykładowe opisy posiłków (krótkie/ambiguous/edge), różne daty do raportów.

