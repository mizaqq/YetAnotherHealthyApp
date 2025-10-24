## Tech Stack

YetAnotherHealthyApp to webowa aplikacja do szybkiego zapisywania posiłków oraz monitorowania kalorii i makroskładników. Poniżej opis aktualnego stosu technologicznego zgodnego z repozytorium.

### Frontend — React 19 (Vite)

- **React 19**: główny framework SPA, interaktywność tylko tam, gdzie jest potrzebna.
- **Vite**: bardzo szybkie uruchamianie środowiska developerskiego i bundling produkcyjny.
- **TypeScript 5**: statyczne typowanie i lepszy DX.
- **Tailwind CSS 4**: stylowanie w podejściu utility‑first.
- **Struktura**: kod w `apps/frontend`, źródła w `apps/frontend/src`, klienci przeglądarkowi w `apps/frontend/src/lib`, build w `apps/frontend/dist`, konfiguracje w `apps/frontend/vite.config.ts`, `apps/frontend/tailwind.config.js`, `apps/frontend/eslint.config.js`, `apps/frontend/tsconfig.json`.

### Backend — FastAPI 0.119.0 (Python)

- **FastAPI 0.119.0**: warstwa REST API.
- **Struktura**:
  - Endpointy: `apps/backend/app/api/v1/` (np. `endpoints/health.py`).
  - Konfiguracja i infrastruktura: `apps/backend/app/core/` (np. `config.py`).
  - Połączenia/SESJE DB: `apps/backend/app/db/` (np. `session.py`).
  - Logika domenowa i orkiestracja: `apps/backend/app/services/`.
  - Modele i schematy: `apps/backend/app/models/`, `apps/backend/app/schemas/`.
  - Punkt wejścia aplikacji: `apps/backend/app/main.py`.
  - Konfiguracja projektu: `apps/backend/pyproject.toml`; testy: `apps/backend/tests/`.

### AI — Integracja przez OpenRouter

- **OpenRouter** ([openrouter.ai](https://openrouter.ai)): dostęp do szerokiej gamy modeli (OpenAI, Anthropic, Google i inne) z kontrolą kosztów i limitami per klucz API.
- **Integracja**: rekomendowana po stronie backendu (FastAPI) jako serwis w `app/services/` z konfiguracją w `app/core/config.py` i sekrety poprzez zmienne środowiskowe.

### CI/CD i Hosting

- **GitHub Actions**: budowanie i testy w pipeline CI; opcjonalnie publikacja obrazów Docker.
- **Docker**: obrazy do uruchomienia zarówno lokalnie, jak i w chmurze.
- **DigitalOcean**: hosting (np. App Platform lub Droplet) dla frontend+backend.
- **Środowiska/sekrety**: trzymane jako zmienne środowiskowe w CI i na platformie hostingu.
