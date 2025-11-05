## Frontend Auth – plan integracji (React × Supabase-js × FastAPI proxy)

### Cel

- Zintegrować istniejące komponenty auth z backendowymi proxy.
- Zapewnić pełne przepływy: rejestracja, potwierdzenie email, logowanie, reset hasła.
- Zgodność z PRD (US-001, US-002) oraz specyfikacją `.ai/auth-spec.md`.

### Założenia środowiskowe

- `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` skonfigurowane (wymagane przez `supabaseClient.ts`).
- `VITE_API_BASE=http://127.0.0.1:54321/api/v1` (dev) – wykorzystywane w `lib/api.ts`.
- Supabase config: enable_confirmations=true; redirect: `/reset-password/confirm`, `/email-confirmation`.

### Zmiany w hooku `useAuth`

- Plik: `apps/frontend/src/hooks/useAuth.ts`.

1. `login(data)`: pozostaje przez `supabase.auth.signInWithPassword` (zachowuje sesję Supabase-js i spójność UI).

2. `register(data)`: wywołaj backend `POST /auth/register`:

   - Dodaj funkcję `postAuthRegister` w `lib/api.ts` (bez Authorization).
   - Po sukcesie: `navigate("/email-confirmation", { state: { email: data.email } })`.
   - Mapuj 409 → „Adres email jest już zajęty.”; inne błędy → komunikat ogólny.

3. `requestPasswordReset({ email })`: nowa funkcja wywołująca `POST /auth/password/reset-request` (bez Authorization):

   - Dodaj `postAuthPasswordResetRequest` w `lib/api.ts`.
   - UI: zawsze sukces (neutralny komunikat) – komponent `ResetPasswordRequestForm` już to wspiera przez `isSubmitSuccessful`.

4. `resetPassword({ password })`: nowa funkcja wywołująca `POST /auth/password/reset-confirm`:

   - Wykorzystuje `authenticatedFetch` (recovery session token w nagłówku Authorization zapewniany przez Supabase-js po wejściu z linku).
   - Po 204: `await supabase.auth.signOut(); navigate("/login")`.

5. Mapowanie błędów Supabase/HTTP:
   - Sign-in: „Nieprawidłowy email lub hasło.” dla `Invalid login credentials`.
   - Register: 409 → „Adres email jest już zajęty.”, inne → ogólny komunikat.
   - Reset-confirm: 401 → „Link resetowania nieprawidłowy lub wygasł.”.

### `AuthProvider` – obsługa nawigacji i eventów

- Plik: `apps/frontend/src/lib/AuthProvider.tsx`.

1. Rozszerz listę stron auth:

   - `const AUTH_PAGES = ["/login", "/register", "/reset-password", "/reset-password/confirm", "/email-confirmation"];`

2. Obsługa eventu `PASSWORD_RECOVERY`:

   - W `onAuthStateChange` rozpoznaj `event === "PASSWORD_RECOVERY"` → ustaw stan `isPasswordRecovery = true` i `navigate("/reset-password/confirm")`.
   - Upublicznij w kontekście: `{ session, loading, isPasswordRecovery }`.

3. Nawigacja po zalogowaniu:
   - Jeżeli profil bez `onboarding_completed_at` → `/onboarding`.
   - Jeżeli zalogowany na stronie auth → `/`.
   - Jeżeli brak sesji i strona nieauth → `/login`.

### `api.ts` – nowe funkcje

- Plik: `apps/frontend/src/lib/api.ts`.

Dodaj:

```ts
export async function postAuthRegister(payload: {
  email: string;
  password: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await handleApiError(response);
}

export async function postAuthPasswordResetRequest(payload: {
  email: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/password/reset-request`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await handleApiError(response);
}

export async function postAuthPasswordResetConfirm(payload: {
  password: string;
}): Promise<void> {
  const response = await authenticatedFetch(
    `${API_BASE}/auth/password/reset-confirm`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
  if (!response.ok) await handleApiError(response);
}
```

### Komponenty i strony

- `AuthForm.tsx` – bez zmian funkcjonalnych (toggle `type="button"` już jest; link „Nie pamiętasz hasła?” → `/reset-password`).
- `RegisterPage.tsx` – używa `useAuth().register`; po sukcesie użytkownik widzi `/email-confirmation`.
- `EmailConfirmationPage.tsx` i `EmailConfirmationView.tsx` – prezentują informację i CTA do logowania/ponownej rejestracji.
- `ResetPasswordRequestPage.tsx` / `ResetPasswordRequestForm.tsx` – po submit: success banner (neutralny), niezależnie od istnienia adresu.
- `ResetPasswordConfirmPage.tsx` / `ResetPasswordConfirmForm.tsx` – wysyła nowe hasło do backendu; po 204: `signOut()` i redirect do `/login`. Gdy `!isPasswordRecovery`: renderuje komunikat o nieprawidłowym linku (już zaimplementowane).

### Zgodność z PRD

- US-001: rejestracja z potwierdzeniem emaila; logowanie dopiero po potwierdzeniu; onboarding po zalogowaniu.
- US-002: logowanie – ogólny komunikat przy błędnych danych; dostęp do danych tylko z ważnym JWT.

### Testy akceptacyjne (UI)

1. Rejestracja → `/email-confirmation` → próba logowania bez potwierdzenia (blokada) → po potwierdzeniu logowanie → `/onboarding`.
2. Logowanie błędne → „Nieprawidłowy email lub hasło.”.
3. Reset hasła: request (success banner), link recovery → confirm (204) → redirect `/login`.
4. Zalogowany przechodzi na `/login`/`/register` → redirect `/`.

### Checklist implementacyjny (frontend)

1. Dodać funkcje `postAuthRegister`, `postAuthPasswordResetRequest`, `postAuthPasswordResetConfirm` w `lib/api.ts`.
2. Rozszerzyć `useAuth` o `register`, `requestPasswordReset`, `resetPassword` z wywołaniami powyższych.
3. Rozszerzyć `AuthProvider` o `AUTH_PAGES` i obsługę `PASSWORD_RECOVERY` + `isPasswordRecovery` w kontekście.
4. Ustawić `VITE_API_BASE` na `http://127.0.0.1:54321/api/v1` w `.env.local` (dev).
5. Zweryfikować ścieżki routingu: `/reset-password`, `/reset-password/confirm`, `/email-confirmation` istnieją i są publiczne.
