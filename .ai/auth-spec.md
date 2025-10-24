## Specyfikacja architektury modułu autentykacji (US-001, US-002)

### Kontekst i założenia

- **Stack:** React 19 (Vite, TypeScript 5, Tailwind 4, fluent-2-ui), backend FastAPI 0.119.0, Supabase (Auth + DB z RLS).
- **Stan obecny (frontend):** SPA z `react-router-dom`, `AuthProvider` oparty o `supabase-js` i routy: `/login`, `/register`, `/onboarding`, reszta w układzie aplikacyjnym. Formularz logowania/rejestracji w komponencie `AuthForm` już istnieje.
- **Stan obecny (backend):** Autoryzacja oparta o nagłówek `Authorization: Bearer <jwt>`; walidacja tokenu przez Supabase w zależności `get_current_user_id`. Dostęp do profilu przez `/api/v1/profile` i onboarding przez `/api/v1/profile/onboarding`.
- **Wymagania PRD:**
  - US-001: rejestracja z potwierdzeniem emaila; po kliknięciu linku potwierdzającego użytkownik może się zalogować i jest przekierowywany do ustawienia celu kalorycznego.
  - US-002: logowanie i dostęp tylko do własnych danych; nieujawnianie, które pole (email/hasło) było niepoprawne.

## 1. Architektura interfejsu użytkownika

### 1.1. Widoki, routing i layouty

- **Strony auth (bez AppLayout):**
  - `/login` – logowanie (komponent `LoginPage`) z `AuthForm` w trybie `login`.
  - `/register` – rejestracja (komponent `RegisterPage`) z `AuthForm` w trybie `register`.
  - `/reset-password` – żądanie resetu hasła (nowa strona; prosty formularz z polem email).
  - `/reset-password/confirm` – ustawienie nowego hasła po wejściu z linku e-mail (nowa strona; pola: nowe hasło + potwierdzenie).
- **Strony po zalogowaniu (z `AppLayout`):**
  - `/` (Dashboard), `/history`, `/profile` – już istnieją i są chronione przez `AuthProvider` (autogating + nawigacja).
  - `/onboarding` – ustawienie celu kalorycznego po pierwszym zalogowaniu (już istnieje; auth wymagany).

Nawigacja i gating:

- `AuthProvider` utrzymuje sesję Supabase i decyduje o przekierowaniach:
  - gdy brak sesji → przekierowanie na `/login` z wyjątkiem stron auth (`/login`, `/register`, `/reset-password`, `/reset-password/confirm`).
  - gdy jest sesja, ale brak zakończonego onboardingu → przekierowanie na `/onboarding`.
  - gdy jest sesja i użytkownik odwiedza `/login` lub `/register` → przekierowanie na `/`.
  - obsłuż zdarzenie resetu hasła (Supabase `PASSWORD_RECOVERY`) → przekieruj na `/reset-password/confirm`.

### 1.2. Komponenty i odpowiedzialności

- `AuthForm` (re-używany dla logowania i rejestracji):
  - Odpowiada za zebranie danych, walidację klienta (zod) i wywołanie `onSubmit`.
  - Nie wykonuje nawigacji – sukces obsługuje `AuthProvider` po zmianie sesji.
- `AuthPageLayout` (layout stron auth):
  - Minimalny layout (branding, CTA, linki do zmiany trybu), bez elementów aplikacyjnych z `AppLayout`.
- `useAuth` (hook):
  - Zapewnia `login`, `register`, (nowe) `requestPasswordReset`, `resetPassword` oraz mapowanie błędów Supabase do komunikatów po polsku.
- `AuthProvider`:
  - Utrzymuje `session`, subskrybuje `onAuthStateChange`, pobiera profil po zalogowaniu (`getProfile`) i dokonuje przekierowań.
  - Rozszerzenie: obsługa `PASSWORD_RECOVERY` (nawigacja do `/reset-password/confirm`).

### 1.3. Walidacja i komunikaty błędów

- Formularz rejestracji: hasło min. 8 znaków, co najmniej 1 litera i 1 cyfra (spełnia PRD US-001). Email w formacie RFC, oba pola przycięte (`trim`).
- Formularz logowania: email poprawny, hasło wymagane (może być minimalnie 1 znak – nie naruszamy istniejącego działania; opcjonalnie walidacja dłuższa po stronie serwera).
- Reset hasła – nowe hasło z tymi samymi zasadami co rejestracja.
- Komunikaty:
  - Logowanie: „Nieprawidłowy email lub hasło.” niezależnie od tego, które pole jest błędne (US-002).
  - Rejestracja: jasne komunikaty z walidacji (np. „Hasło musi zawierać…”).
  - Błędy sieci/serwera: „Wystąpił nieoczekiwany błąd. Spróbuj ponownie.”

### 1.4. Scenariusze kluczowe

- Użytkownik zalogowany otwiera `/login` → nic nie renderujemy (SSR/LCP optymalizacja) i `AuthProvider` od razu przekierowuje do `/`.
- Pierwsze logowanie (brak profilu) → `AuthProvider` przechodzi do `/onboarding`.
- Rejestracja → po wypełnieniu formularza użytkownik otrzymuje komunikat "Sprawdź swoją skrzynkę pocztową" i musi kliknąć link potwierdzający w emailu. Po potwierdzeniu może się zalogować.
- Pierwsze logowanie po potwierdzeniu emaila → przekierowanie do `/onboarding` do ustawienia celu kalorycznego.
- Reset hasła:
  1. `/reset-password`: podanie email → `supabase.auth.resetPasswordForEmail` z `redirectTo` na `/reset-password/confirm`.
  2. Po kliknięciu w link z maila → sesja recovery + `/reset-password/confirm` → `supabase.auth.updateUser({ password })` → przekierowanie do `/login` (lub automatyczne zalogowanie, zależnie od polityki Supabase).

## 2. Logika backendowa

### 2.1. Endpointy i kontrakty API (powiązane z auth)

- Auth obsługuje Supabase (brak własnych endpointów login/register) – backend wymaga nagłówka `Authorization: Bearer <jwt>` dla zasobów chronionych.
- Kluczowe istniejące endpointy:
  - `GET /api/v1/profile` → profil użytkownika (używany przez `AuthProvider` do decyzji o onboardingu).
  - `PATCH /api/v1/profile` → aktualizacja np. celu kalorycznego.
  - `POST /api/v1/profile/onboarding` → zakończenie onboardingu.
  - `GET /api/v1/health` → status API (do ewentualnych preflight/sprawdzeń dostępności).
- Opcjonalne endpointy proxy (jeśli chcemy ukrywać szczegóły Supabase od klienta):
  - `POST /api/v1/auth/password/reset-request` { email } → 202/204, bez ujawniania czy email istnieje.
  - `POST /api/v1/auth/password/reset-confirm` { token, new_password } → 204; walidacja tokenu po stronie backendu przez Supabase Admin API.
  - W MVP zalecane korzystanie z `supabase-js` bezpośrednio z frontu; proxy można dodać później (większa złożoność operacyjna i zabezpieczeń).

### 2.2. Walidacja danych wejściowych

- Wszystkie zasoby chronione korzystają z dependency `get_current_user_id` do walidacji JWT i wyciągnięcia `sub` jako `UUID` użytkownika.
- Schematy Pydantic przy endpointach profilu (spójne komunikaty 422). Pola ilościowe (np. `daily_calorie_goal`) walidowane (wartość > 0 itp.).

### 2.3. Obsługa wyjątków i błędów

- Brak/malformowany nagłówek Authorization → 401 z `WWW-Authenticate: Bearer`.
- Token wygasły/nieprawidłowy → 401.
- Brak profilu → 404 (lub 200 z nullem, jeśli wymagamy łagodności – obecnie stosowane jest 404 w UI jako sygnał do onboardingu; UI już to obsługuje stosownym komunikatem).
- Pozostałe błędy → 5xx z logowaniem po stronie serwera.

## 3. System autentykacji – Supabase

### 3.1. Rejestracja, logowanie, wylogowanie

- Frontend: `useAuth` wywołuje `supabase.auth.signUp` i `supabase.auth.signInWithPassword`.
- Konfiguracja Supabase: `enable_confirmations = true` w config.toml wymaga potwierdzenia emaila przed pierwszym zalogowaniem (zgodnie z zaktualizowanym US-001).
- Po rejestracji użytkownik widzi komunikat "Sprawdź swoją skrzynkę pocztową" i nie jest automatycznie zalogowany.
- Po kliknięciu linku z emaila użytkownik może się zalogować i zostaje przekierowany do `/onboarding`.
- Wylogowanie: `supabase.auth.signOut()` z domknięciem stanu w `AuthProvider` (nawigacja na `/login`).

### 3.2. Reset hasła

- Żądanie: `supabase.auth.resetPasswordForEmail(email, { redirectTo: <APP_ORIGIN>/reset-password/confirm })`. Zwracamy neutralny komunikat (zawsze sukces), by nie ujawniać, czy email jest zarejestrowany.
- Potwierdzenie: po wejściu z linku e-mail Supabase emituje event `PASSWORD_RECOVERY` i wprowadza sesję recovery. Na stronie `/reset-password/confirm` wywołujemy `supabase.auth.updateUser({ password: newPassword })`. Następnie:
  - jeśli polityka pozwala, można automatycznie zalogować; w MVP bardziej przewidywalne jest przekierowanie na `/login` i klasyczne zalogowanie.

### 3.3. Bezpieczeństwo i RLS

- Backend używa Supabase Service Role tylko po stronie serwera (ukryty klucz). Token użytkownika weryfikowany jest per żądanie przez `get_current_user_id` (Supabase Admin API `auth.get_user`).
- Wszystkie zapytania do tabel użytkownika w Supabase powinny mieć RLS wymuszające `user_id = auth.uid()`.
- Klient (frontend) zawsze do backendu przesyła `Authorization: Bearer <jwt>` (patrz wrapper `authenticatedFetch`).

## 4. Kontrakty UI ↔ API i separacja odpowiedzialności

### 4.1. Formularze React (client)

- Walidacja klienta (zod), UX (disabled submit gdy invalid/loading), dostępność (aria-\*), mapowanie błędów Supabase do krótkich komunikatów.
- Brak bezpośredniej nawigacji po submit – czekamy na `onAuthStateChange` i logikę w `AuthProvider`.
- Reset hasła obsługiwany w pełni przez `supabase-js` po stronie klienta, bez dotykania backendu (MVP).

### 4.2. Strony (routing) i layouty

- Strony auth renderowane z `AuthPageLayout`, bez bocznych paneli i elementów danych.
- Strony po zalogowaniu renderowane wewnątrz `AppLayout`; dane ładowane przez dedykowane hooki (`useDashboardData`, `useProfile`, etc.).

### 4.3. Backend

- Brak własnego `POST /login` i `POST /register` – integracja z Supabase eliminuje ten obowiązek.
- `GET /profile` jako punkt prawdy o stanie onboardingu. 401/404 prowadzą do odpowiedniego UX (przekierowanie / komunikaty).

## 5. Usprawnienia i weryfikacja istniejącego `AuthForm.tsx`

### 5.1. Co działa poprawnie

- Walidacja rejestracji spełnia PRD (min. 8 znaków, litera i cyfra).
- `AuthForm` nie nawiguję sam – polega na `AuthProvider`.
- A11y: etykiety, `aria-invalid`, `aria-describedby`, `role=alert` dla błędów API.

Przykładowe fragmenty z kodu:

```135:150:apps/frontend/src/components/auth/AuthForm.tsx
<Label htmlFor="email">Email</Label>
<Input
  id="email"
  type="email"
  autoComplete="email"
  {...register("email")}
  aria-invalid={errors.email ? "true" : "false"}
  aria-describedby={errors.email ? "email-error" : undefined}
/>
{errors.email && (
  <Text id="email-error" className={styles.errorText}>
    {errors.email.message}
  </Text>
)}
```

```152:168:apps/frontend/src/components/auth/AuthForm.tsx
<Input
  id="password"
  type={showPassword ? "text" : "password"}
  autoComplete={mode === "login" ? "current-password" : "new-password"}
  contentAfter={
    <Button
      appearance="transparent"
      className={styles.passwordToggle}
      onClick={() => setShowPassword(!showPassword)}
      icon={showPassword ? <EyeOffRegular /> : <EyeRegular />}
      aria-label={showPassword ? "Ukryj hasło" : "Pokaż hasło"}
      tabIndex={-1}
    />
  }
  {...register("password")}
  aria-invalid={errors.password ? "true" : "false"}
  aria-describedby={errors.password ? "password-error" : undefined}
/>
```

### 5.2. Zalecane usprawnienia (bez zmiany kontraktu UX)

- Dodać link „Nie pamiętasz hasła?” w stopce formularza kierujący do `/reset-password`.
- W przycisku do przełączania widoczności hasła ustawić jawnie `type="button"`, aby nigdy nie zainicjował submit (bezpieczne mimo użycia Fluent UI):
  - Obecnie przycisk jest osadzony w `contentAfter` i używa `onClick`, ale jawne `type` eliminuje ryzyko.
- Preprocessing pól w zod: `z.string().trim()` dla email/hasła (uniknięcie przypadkowych spacji).
- Mapowanie błędów Supabase do komunikatów po polsku w `useAuth` (np. `Invalid login credentials` → „Nieprawidłowy email lub hasło.”; brak ujawniania, które pole jest niepoprawne – US-002).
- W `AuthProvider` obsłużyć event `PASSWORD_RECOVERY` z `supabase.auth.onAuthStateChange` i wykonać `navigate("/reset-password/confirm")`.
- (Opcjonalnie) dodać licznik prób i krótkie opóźnienie po błędach logowania po stronie UI.

## 6. Zmiany w kodzie (przegląd – bez implementacji w tej specyfikacji)

### Frontend (nowe/rozszerzenia)

- Nowe strony/komponenty:
  - `pages/auth/ResetPasswordRequestPage.tsx` – formularz email.
  - `pages/auth/ResetPasswordConfirmPage.tsx` – formularz nowego hasła.
  - Rozszerzyć `useAuth` o `requestPasswordReset(email)` i `resetPassword(newPassword)`.
  - Rozszerzyć `AuthProvider` o obsługę `PASSWORD_RECOVERY` i dopuszczenie ścieżek resetu w logice przekierowań.
  - Dodać link w `AuthForm` do `/reset-password` (tylko w trybie `login`).

### Backend

- Brak zmian wymaganych dla login/register (Supabase Auth).
- (Opcjonalnie) wprowadzić proxy endpointy dla resetu hasła, jeśli chcemy przenieść odpowiedzialność z frontu na backend (wymaga użycia Supabase Admin API i dbałości o rate limits/security).

## 7. Wymagania niefunkcjonalne i bezpieczeństwo

- RLS w Supabase gwarantuje izolację danych użytkowników – utrzymywać zasady `user_id = auth.uid()`.
- Token JWT nigdy nie jest logowany po stronie serwera ani klienta.
- CORS już skonfigurowany dla dev; doprecyzować listę originów dla prod.
- Błędy wrażliwe mapować do neutralnych komunikatów; szczegóły logować na serwerze.

## 8. Zależności konfiguracyjne Supabase (kluczowe dla US-001)

- W projekcie Supabase włączyć `enable_confirmations = true` w config.toml, aby wymagać potwierdzenia emaila przed pierwszym zalogowaniem (zgodnie z zaktualizowanym US-001).
- Skonfigurować `Site URL` i `Redirect URLs` tak, by zawierały:
  - `http://127.0.0.1:3000/reset-password/confirm`
  - `http://localhost:5173/reset-password/confirm` (Vite dev server)
  - Ewentualnie inne varianty dla środowiska produkcyjnego.

## 9. Kontrakty danych (skrót)

- Nagłówek do żądań chronionych: `Authorization: Bearer <access_token>`.
- `ProfileDTO` (używany w UI): `{ user_id: string; daily_calorie_goal: number | null; onboarding_completed_at: string | null; timezone: string; ... }`.
- Błędy backendu: JSON/tekst; UI mapuje 401 → „Zaloguj się ponownie”, 404 profilu → „Uzupełnij onboarding”.

## 10. Testowalność i kryteria akceptacji

- Rejestracja: poprawny email + hasło spełniające reguły → komunikat "Sprawdź skrzynkę pocztową"; po kliknięciu linku w emailu użytkownik może się zalogować.
- Pierwsze logowanie po potwierdzeniu emaila → redirect do `/onboarding`.
- Logowanie bez potwierdzonego emaila → komunikat błędu.
- Logowanie: poprawne dane → `/` lub `/onboarding` w zależności od profilu; błędne dane → ogólny komunikat o błędzie bez wskazywania pola.
- Reset hasła: żądanie zawsze zwraca neutralny komunikat; ustawienie nowego hasła działa dla poprawnego linku recovery.
- Brak sesji → ochrona zasobów aplikacji i redirect do `/login`.

---

Dokument przygotowano na podstawie aktualnego kodu i PRD. Specyfikacja nie wprowadza zmian łamiących istniejące działanie; proponowane rozszerzenia (reset hasła, event recovery, mapowanie błędów) są kompatybilne wstecznie.
