## Backend Auth – plan integracji (FastAPI × Supabase)

### Cel

- Zapewnić proxy endpointy Auth w FastAPI, z separacją kluczy i logiki od frontendu.
- Zgodność z PRD (US-001, US-002) i regułami backend/shared.

### Założenia środowiskowe

- Supabase Auth: enable_confirmations = true; site_url = "http://localhost:5173"; additional_redirect_urls zawiera `http://localhost:5173/reset-password/confirm`, `http://localhost:5173/email-confirmation`.
- RLS wyłączone na dev (na prod włączone); backend weryfikuje JWT przez Supabase Admin API.
- Backend dev URL: `http://127.0.0.1:54321` z prefiksem API `/api/v1`.
- Sekrety w `.env`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (używane wyłącznie po stronie serwera).

### Architektura i dobre praktyki

- FastAPI: asynchroniczne endpointy, Pydantic v2 modele request/response, DI (dependencies), jednolite błędy przez `HTTPException`.
- Walidacja wejścia na początku (guard clauses). Brak ujawniania wrażliwych informacji (np. istnienia konta przy reset-request).
- Obsługa JWT: `Authorization: Bearer <jwt>` – weryfikacja przez `client.auth.get_user(token)` (Supabase Admin) w dependency `get_current_user_id`.
- CORS: dopuszczone `http://localhost:5173` i `http://127.0.0.1:5173` (już skonfigurowane w `app/main.py`).

### Nowe endpointy (router `auth`)

- Lokalizacja: `apps/backend/app/api/v1/endpoints/auth.py`.
- Rejestracja routera w `app/api/v1/api.py`: `include_router(endpoints.auth.router, prefix="/auth", tags=["auth"])`.

1. POST `/api/v1/auth/register`

   - Body: `{ email: EmailStr, password: str }` (Pydantic schema: `RegisterCommand`).
   - Działanie: utwórz użytkownika przez `client.auth.admin.create_user(...)` z parametrami:
     - `email`, `password`;
     - `email_confirm` = False (wymagamy potwierdzenia);
     - `redirect_to` = `http://localhost:5173/email-confirmation` lub `http://localhost:5173/login` (spójnie z polityką UX; rekomendacja: `/login`).
   - Zwraca: `201 Created` → `{ message: "Check your email" }`.
   - Błędy:
     - Email zajęty → `409 Conflict` → `{ detail: "Email already in use" }`.
     - Pozostałe → `400/500` zgodnie z przyczyną.

2. POST `/api/v1/auth/password/reset-request`

   - Body: `{ email: EmailStr }` (schema: `ResetPasswordRequestCommand`).
   - Działanie: `client.auth.reset_password_for_email(email, redirect_to="http://localhost:5173/reset-password/confirm")`.
   - Zwraca zawsze neutralnie: `202 Accepted` → `{ message: "If the account exists, a reset link was sent" }`.
   - Nigdy nie ujawnia, czy email istnieje.

3. POST `/api/v1/auth/password/reset-confirm`

   - Headers: `Authorization: Bearer <jwt>` (recovery session z linku Supabase).
   - Body: `{ password: str }` (schema: `ResetPasswordConfirmCommand`).
   - Działanie:
     - Wyciągnij `user_id` przez dependency `get_current_user_id` (walidacja tokenu recovery).
     - `client.auth.admin.update_user_by_id(user_id, { password })`.
   - Zwraca: `204 No Content`.
   - Błędy: nieważny/wygasły link → `401`.

4. (Opcjonalnie – backlog) POST `/api/v1/auth/login`
   - Alternatywa dla logowania po stronie klienta: `client.auth.sign_in_with_password` i zwrot pary tokenów do frontu (front wywołuje `supabase.auth.setSession(...)`).
   - W MVP pozostawiamy logowanie w kliencie Supabase-js dla prostoty utrzymania sesji.

### Schematy danych (Pydantic v2)

- `RegisterCommand`: `{ email: EmailStr, password: constr(min_length=8) }` + walidacja złożoności (litera+cyfra).
- `ResetPasswordRequestCommand`: `{ email: EmailStr }`.
- `ResetPasswordConfirmCommand`: `{ password: constr(min_length=8, regexes=[letter, digit]) }`.
- (Opcjonalnie) `MessageResponse`: `{ message: str }`.

### Integracja z istniejącym kodem

- Wykorzystaj istniejące:
  - `get_supabase_client()` – zwraca klienta z Service Role Key.
  - `get_current_user_id()` – walidacja/parsowanie JWT.
- Dodaj `schemas/auth.py` z modelami Pydantic.
- Zarejestruj router `auth` w `app/api/v1/api.py`.

### Mapowanie błędów i kody odpowiedzi

- 201 (register), 202 (reset-request), 204 (reset-confirm), 401 (token invalid/expired), 409 (email exists), 400/422 (walidacja), 5xx (awarie).
- Treść błędów: krótkie, użytkowe; bez ujawniania szczegółów technicznych.

### Bezpieczeństwo

- Service Role Key wyłącznie w backendzie.
- Brak logowania tokenów/sekretów.
- Neutralne odpowiedzi dla reset-request.
- Rate limiting (opcjonalnie) i logowanie prób (INFO/WARN) bez danych wrażliwych.

### Testy (API)

- Register: 201 dla nowego email, 409 dla istniejącego.
- Reset-request: zawsze 202 (niezależnie od istnienia konta).
- Reset-confirm: 204 dla poprawnego recovery tokenu; 401 dla błędnego/wygasłego.

### Powiązanie z PRD

- US-001: rejestracja z potwierdzeniem emaila; po potwierdzeniu możliwość logowania.
- US-002: logowanie bez ujawniania, które pole jest błędne (mapowanie po stronie UI; backend nie rozróżnia w komunikatach wrażliwych przypadków).

### Checklist implementacyjny

1. Utwórz `app/api/v1/schemas/auth.py` z modelami: RegisterCommand, ResetPasswordRequestCommand, ResetPasswordConfirmCommand, MessageResponse.
2. Utwórz `app/api/v1/endpoints/auth.py` z trzema endpointami (async, DI, Supabase calls, walidacja błędów).
3. Zarejestruj router w `app/api/v1/api.py`.
4. Upewnij się, że `app/main.py` eksportuje router pod `/api/v1` (już jest) i CORS obejmuje dev originy.
5. Dodaj testy jednostkowe/integracyjne dla nowych endpointów.
6. Zweryfikuj `apps/supabase/config.toml` (enable_confirmations, redirect URLs) – zgodnie z konfiguracją podaną przez Ciebie.
7. (Prod) Włączyć RLS i polityki – zgodnie z `supabase-migration.mdc`.

### Notatki dot. Supabase

- Python SDK (supabase>=2.22.0) – używaj przestrzeni `auth` i `auth.admin` zgodnie z dokumentacją wersji.
- `reset_password_for_email` powinno przyjmować `redirect_to` wskazujące `/reset-password/confirm`.
- Drobne różnice nazw metod/parametrów między SDK – podczas implementacji zweryfikować w aktualnej dokumentacji.
