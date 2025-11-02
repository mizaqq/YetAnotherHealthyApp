## Zasady CI/CD w GitHub Actions – YetAnotherHealthyApp

Zakres: monorepo z `apps/frontend` (React 19, Vite, Vitest, Playwright) oraz `apps/backend` (FastAPI 0.119, Python 3.13, uv). Poniższe zasady są oparte na 10xRules dla: GitHub Actions, Monorepo, Playwright, PyTest, Vitest oraz dostosowane do dostępnych skryptów i Makefile w repozytorium.

### Ogólne

- **Główne wersje akcji**: zawsze przypinaj do głównych wersji (`actions/checkout@v4`, `actions/setup-node@v4`, `astral-sh/setup-uv@v3` lub nowsze major). Okresowo aktualizuj do najnowszych major.
- **Instalacja zależności (Node)**: używaj wyłącznie `npm ci`.
- **Instalacja zależności (Python/uv)**: uruchamiaj `uv sync --locked --all-groups` w katalogu backendu; testy przez `uv run pytest`.
- **Zmienne środowiskowe**: definiuj na poziomie jobów (nie globalnie w workflow). Nigdy nie ujawniaj sekretów w logach.
- **Gałąź główna**: zweryfikuj czy repo używa `main` (a nie `master`) i używaj konsekwentnie w `on.push.branches`.
- **Czas działania i bezpieczeństwo**: ustaw `timeout-minutes` (np. 15) i minimalne `permissions:` (np. `contents: read`). Dla wdrożeń używaj OIDC oraz minimalnych uprawnień per job.
- **Wspólne kroki**: jeśli kroki powtarzają się w wielu jobach/workflow, wyodrębnij je do **Composite Actions** w `.github/actions/` (np. `setup-frontend`, `setup-backend`).
- **Równoległość i anulowanie**: dla PR ustaw `concurrency` z `cancel-in-progress: true` na klucz `workflow + ref`.
- **Artefakty i raporty**: publikuj raporty (coverage, Playwright report) jako artefakty; ustaw retencję (np. 7 dni).

### Struktura workflow (zalecana)

- **PR Checks** (na `pull_request`):
  - FE: lint (`npm run lint`), typecheck (`npm run typecheck`), testy jednostkowe (`npm run test` lub `test:coverage`), build (`npm run build`).
  - BE: lint (`uv run ruff check`), testy (pytest z coverage), opcjonalnie sprawdzenie importów/typów jeśli wymagane.
  - E2E: Playwright (Chromium) – uruchamiaj:
    - na żądanie (label `e2e`),
    - lub w nocnym harmonogramie (`schedule`) i/lub na `pull_request` dla kluczowych ścieżek.
- **E2E** (oddzielny workflow, na żądanie/cron): Playwright tylko Chromium, zgodnie z zasadami E2E.
- **Release/Deploy** (na `push` do `main` i/lub `tags`): build artefaktów FE i BE; wdrożenia z OIDC i minimalnymi uprawnieniami. (Miejsce docelowe wdrożeń do ustalenia – doprecyzuj w ADR.)

### Selektywne uruchamianie w monorepo

- Stosuj `paths`/`paths-ignore`, aby uruchamiać tylko to, co dotyczy zmian:
  - Zmiany w `apps/frontend/**` → joby FE.
  - Zmiany w `apps/backend/**` → joby BE.
  - Zmiany w plikach wspólnych (np. `Makefile`, `.github/**`) → odpowiednie joby obu aplikacji.

### Zasady dla Frontendu (React/Vite)

- **Środowisko Node**: używaj `actions/setup-node@v4` z `node-version: '20'` (lub wybrana LTS) oraz `cache: 'npm'` i `cache-dependency-path: 'apps/frontend/package-lock.json'`.
- **Instalacja**: `npm ci` w `apps/frontend`.
- **Jakość**:
  - Lint: `npm run lint` (zero ostrzeżeń).
  - Typecheck: `npm run typecheck`.
- **Testy jednostkowe**:
  - `npm run test` (lub `test:coverage`), publikuj artefakty coverage.
  - Reguły Vitest: stosuj `vi.fn()/spyOn`, konfigurację w `vitest.config.ts`, sensowne progi coverage (bez fetyszyzacji %).
- **Build**: `npm run build`, publikuj `dist/` jako artefakt.
- **Cache Playwright**: przed E2E zainstaluj przeglądarkę: `npx playwright install --with-deps chromium` (Linux runners).

### Zasady dla Backend (FastAPI, uv)

- **Środowisko Python/uv**: używaj `astral-sh/setup-uv@v3` (lub nowsze major) oraz `python-version: '3.13'`.
- **Instalacja**: w `apps/backend` wykonaj `uv sync --locked --all-groups` (zależności prod/dev/test wg `pyproject.toml` i `uv.lock`).
- **Lint**: `uv run ruff check` (rozważ format wyjścia GitHub do anotacji błędów).
- **Testy (PyTest)**:
  - Uruchamiaj pełny zestaw: `uv run pytest` z markerami i coverage (`--cov=app --cov-report=term-missing`).
  - Zasady PyTest: używaj fixtures, markerów (`unit`, `integration`), `asyncio_mode=auto`, parametryzacji.

### Zasady E2E (Playwright)

- **Przeglądarka**: tylko Chromium (Chromium/Desktop Chrome) zgodnie z regułami E2E.
- **Izolacja**: używaj kontekstów przeglądarki per test/suite.
- **Page Object Model**: trzymaj page-objects w `apps/frontend/e2e/pages` (już istnieje struktura `e2e/pages/`).
- **Selektory**: preferuj `data-testid` i `getByTestId`.
- **Wizualne regresje**: stosuj `expect(page).toHaveScreenshot()` dla krytycznych ekranów.
- **Trace/Debug**: włącz trace na niepowodzeniach i publikuj Playwright report jako artefakt.
- **Uruchamianie**: użyj istniejących targetów z `Makefile`:
  - `make test-frontend-e2e` – startuje backend, uruchamia testy, porządkuje procesy.
  - Dla trybu UI i raportów użyj odpowiednich celów (`test-frontend-e2e-ui`, `test-frontend-e2e-report`).

### Wydajność i cache

- **Node**: `actions/setup-node` z cachingiem npm + `npm ci`.
- **uv/Python**: `setup-uv` (cache zależności) + `uv sync --locked --all-groups`.
- **Strategie dodatkowe**: cache Playwright (przeglądarki) między jobami w obrębie workflow, jeśli czas instalacji jest istotny.

### Konwencje YAML (zalecenia)

- **Nazewnictwo**: pliki `.github/workflows/` zgodnie z funkcją: `pr-checks.yml`, `e2e.yml`, `release.yml`.
- **concurrency** dla PR:
  - `group: ${{ github.workflow }}-${{ github.ref }}`
  - `cancel-in-progress: true`
- **permissions** minimalne per job (np. `contents: read`). Dla wdrożeń tylko wymagane uprawnienia (`id-token: write` etc.).
- **timeouts**: ustaw (np. 10–15 min) zależnie od jobu.
- **env**: ustawiaj per job, nie globalnie. Używaj `APP_ENV`, `CI=true` i innych bezpiecznie.

### Selektory ścieżek (przykłady)

- FE joby: `paths: [ 'apps/frontend/**', '.github/**', 'Makefile' ]`
- BE joby: `paths: [ 'apps/backend/**', '.github/**', 'Makefile' ]`
- E2E job (opcja): `paths: [ 'apps/frontend/**', 'apps/backend/**', 'e2e/**', '.github/**' ]` + label/cron.

### Artefakty (zalecane)

- **Frontend**: `apps/frontend/dist` (build), `coverage` (Vitest), `playwright-report`/`traces`.
- **Backend**: `htmlcov` (jeśli generowane) lub raporty coverage, logi z testów.
- Ustal retencję (np. 7 dni) i rozmiary.

### Checklista implementacyjna (kroki)

- [ ] Zweryfikuj branch główny (`main` vs `master`).
- [ ] Dodaj workflow `pr-checks.yml` dla FE/BE z selektywnymi `paths`.
- [ ] Dodaj workflow `e2e.yml` (na żądanie – label `e2e` i/lub `workflow_dispatch`, plus `schedule`).
- [ ] Dodaj workflow `release.yml` (na `push` do `main`/`tags`) i zdefiniuj środowisko docelowe.
- [ ] Użyj `actions/checkout@v4`, `actions/setup-node@v4` (cache npm), `astral-sh/setup-uv@v3`.
- [ ] W FE używaj `npm ci`, potem `lint`, `typecheck`, `test`, `build`.
- [ ] W BE `uv sync --locked --all-groups`, `uv run ruff check`, `uv run pytest --cov`.
- [ ] W E2E zainstaluj Chromium (`npx playwright install --with-deps chromium`) i uruchom `make test-frontend-e2e`.
- [ ] Dodaj `concurrency`, `permissions`, `timeout-minutes` do jobów.
- [ ] Publikuj artefakty (coverage, build, raporty Playwright) i ustaw retencję.

### Notatki 10xRules (dopasowane)

- GitHub Actions: korzystaj z `npm ci`, zmiennych `env:` na poziomie jobów, wyodrębniaj wspólne kroki do composite actions.
- Monorepo: uruchamiaj tylko dotknięte pakiety; centralizuj konfiguracje i cache.
- Playwright: Chromium only, POM, `data-testid`, trace/report jako artefakty.
- PyTest: fixtures, markery, parametryzacja, spójne `pytest.ini`/`pyproject`.
- Vitest: `vi.fn/spyOn`, konfiguracja JSDOM, sensowne progi coverage.

—
Dokument określa zasady. Implementację workflowów oraz ewentualnych composite actions dodaj w `.github/workflows/` oraz `.github/actions/` zgodnie z powyższymi wytycznymi.
