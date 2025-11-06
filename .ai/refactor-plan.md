## Frontend Auth Refactor Plan

### Goals

- Fix prolonged/stale auth state and redirect loops.
- Decouple navigation from auth effects; make auth a single source of truth.
- Ensure clean logout and immediate ability to log in again.
- Normalize password-recovery and token-refresh behavior.

### Problems Today (quick)

- Provider couples navigation with auth and profile fetching; leads to race conditions, stale session reads, and loops.
- Profile fetch runs on every path change, amplifying redirects when 401/404 or network errors occur.
- Inconsistent sign-out (local vs global; sometimes not awaited) can leave session half-alive.
- Password-recovery flag persists and can block normal login unintentionally.

Key spots in current code:

```116:139:apps/frontend/src/lib/AuthProvider.tsx
  useEffect(() => {
    if (loading) return; // Wait until the initial session check is complete

    const handleNavigation = async (): Promise<void> => {
      // SECURITY: If in password recovery mode, ONLY allow access to reset page
      // Recovery sessions should not grant access to the app
      if (isPasswordRecovery) {
        if (location.pathname !== "/reset-password/confirm") {
          console.warn("Blocked navigation during password recovery. Redirecting to reset page.");
          navigate("/reset-password/confirm", { replace: true });
        }
        return;
      }

      // Guard: No session - redirect to login if not on auth page
      if (!session) {
        if (!AUTH_PAGES.includes(location.pathname)) {
          navigate("/login", { replace: true });
        }
        return;
      }

      // User has session - validate it by fetching profile
      try {
        const profile = await getProfile();
```

```171:190:apps/frontend/src/lib/AuthProvider.tsx
        // For 401 unauthorized errors, sign out locally only (don't navigate if already on login)
        const isUnauthorizedError =
          error instanceof Error &&
          (error.message.toLowerCase().includes("unauthorized") ||
            error.message.toLowerCase().includes("401"));

        if (isUnauthorizedError) {
          // Sign out locally to clear the stale token
          await supabase.auth.signOut();
          // Only navigate to login if not already on an auth page
          if (!AUTH_PAGES.includes(location.pathname)) {
            navigate("/login", { replace: true });
          }
          return;
        }

        // For other errors (network issues, etc.), sign out and redirect
        void supabase.auth.signOut();
        navigate("/login", { replace: true });
```

### Proposed Architecture (aligned with tech stack and frontend/react guidelines)

1) Centralize auth state via a store

- Add `apps/frontend/src/lib/authStore.ts` using `useSyncExternalStore`.
- Subscribe once to `supabase.auth.onAuthStateChange` and to initial `getSession()`.
- Track typed status: `"loading" | "unauthenticated" | "authenticated" | "recovery"`.
- Expose: `{ status, session, user, isAuthenticated, isRecovery, signOut, refresh }`.
- Handle events: `SIGNED_IN`, `SIGNED_OUT`, `PASSWORD_RECOVERY`, `TOKEN_REFRESHED`, `USER_UPDATED`.
- Always `await supabase.auth.signOut({ scope: "global" })` for consistency; flip state to `unauthenticated` immediately.

2) Slim `AuthProvider` to presentation-only

- Render loading splash while store status is `loading`.
- Provide store values via context. No navigation, no `getProfile` here, no per-path effects.

3) Route guards for navigation

- Add `apps/frontend/src/routes/ProtectedRoute.tsx`:
  - `unauthenticated` → redirect to `/login`.
  - `recovery` → redirect to `/reset-password/confirm`.
  - `authenticated` → render children.
- Add `apps/frontend/src/routes/PublicRoute.tsx`:
  - If `authenticated` and profile completed → redirect to `/`.
  - Else render children.

4) Fetch profile where needed, not globally

- Add `apps/frontend/src/hooks/useProfile.ts` (SWR or simple cached hook).
- Fetch only when `status === "authenticated"`.
- Handling:
  - 404 → redirect to `/onboarding`.
  - 401 → `await signOut({ scope: "global" })`, then redirect to `/login`.
- Optionally use Suspense boundaries for better UX.

5) Normalize password-recovery flow

- Source of truth is Supabase event `PASSWORD_RECOVERY` and initial URL hash check.
- Persist recovery flag in `sessionStorage` only while tab lives; clear on `SIGNED_OUT` and after successful reset.
- While in recovery, guards allow only `/reset-password/confirm`.
- After reset: clear flag → `signOut({ scope: "global" })` → redirect to `/login?reset=success`.

6) Token expiry and refresh

- Ensure Supabase client uses `persistSession: true` and `autoRefreshToken: true`.
- On `TOKEN_REFRESHED`, keep state as `authenticated`.
- On refresh failure leading to `SIGNED_OUT`, flip to `unauthenticated` without Provider-driven redirects.

7) Error handling and UX

- Keep `apps/frontend/src/hooks/useAuth.ts` as action-only (login/register/reset).
- Do not navigate on success from these hooks; let guards route based on store state.
- Unify error mapping; keep messages user-friendly.

8) Testing (Vitest + Playwright)

- Unit: `authStore` transitions for all events; `ProtectedRoute` and `PublicRoute` behavior.
- E2E:
  - login → dashboard
  - logout → back to login → can log in again
  - token expiry → next API 401 triggers logout → can log in again
  - recovery link → confirm → forced logout → login success

### File/Module Changes

- New: `apps/frontend/src/lib/authStore.ts`
  - Store with `useSyncExternalStore` and Supabase subscriptions.
- New: `apps/frontend/src/routes/ProtectedRoute.tsx`
- New: `apps/frontend/src/routes/PublicRoute.tsx`
- New: `apps/frontend/src/hooks/useProfile.ts`
- Update: `apps/frontend/src/lib/AuthProvider.tsx`
  - Remove navigation and profile fetching side-effects.
  - Provide store state and loading UI only.
- Update: `apps/frontend/src/hooks/useAuth.ts`
  - Keep actions (login/register/request/reset); no success navigation.
  - Use `await supabase.auth.signOut({ scope: "global" })` where applicable.
- Verify: `apps/frontend/src/lib/supabaseClient.ts`
  - Ensure `persistSession: true`, `autoRefreshToken: true`.

### Minimal API Shapes (illustrative)

```ts
// apps/frontend/src/lib/authStore.ts
export type AuthStatus = "loading" | "unauthenticated" | "authenticated" | "recovery";

export function useAuthStatus(): {
  status: AuthStatus;
  session: import("@supabase/supabase-js").Session | null;
  user: import("@supabase/supabase-js").User | null;
  isAuthenticated: boolean;
  isRecovery: boolean;
  signOut: (opts?: { scope?: "local" | "global" }) => Promise<void>;
} { /* impl in file */ }
```

```tsx
// apps/frontend/src/routes/ProtectedRoute.tsx
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  // read status from authStore
  // redirect based on status
  return <>{children}</>;
}
```

```ts
// apps/frontend/src/hooks/useProfile.ts
export function useProfile() {
  // fetch profile when authenticated; handle 401/404
}
```

### Rollout Plan

1. Implement `authStore` and guards; leave Provider unchanged.
2. Migrate routes to use `ProtectedRoute`/`PublicRoute` for a subset (login, dashboard).
3. Introduce `useProfile` and move profile fetch out of Provider.
4. Remove Provider navigation effects; Provider becomes thin.
5. Update `useAuth` to action-only and unify sign-out behavior.
6. Verify Supabase client configuration; add missing flags if needed.
7. Add unit tests for store and guards; update Playwright flows.
8. Remove dead code and logs after verification.

### Acceptance Criteria

- After logout, user is on `/login` and can immediately log in again.
- Token expiry or API 401 leads to automatic sign-out; subsequent login works.
- Recovery flow restricts navigation to `/reset-password/confirm` until completion; then forces logout and shows success on login page.
- No redirect loops; profile fetched only when needed.
- Unit + E2E tests pass for the above scenarios.

### Alignment with project guidelines

- Matches React guidelines: hooks, `useSyncExternalStore`, Suspense-ready, separation of concerns.
- Matches Frontend/Tailwind guidance: accessibility via guards and focused loading UI.
- Matches Tech Stack: Supabase client auto-refresh and persisted sessions; FastAPI profile contract respected.

### Notes/Risks

- Be careful to await global sign-out to avoid half-signed-out states.
- Keep recovery flag ephemeral and always clear on sign-out and after reset.
- Avoid re-fetching profile on every path change; scope to authenticated-only.


