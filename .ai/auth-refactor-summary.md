# Auth Refactoring Summary

## Overview

Successfully refactored the authentication system to eliminate redirect loops, fix stale auth state issues, and properly separate concerns by introducing a centralized auth store with route guards.

## Changes Completed

### 1. New Files Created

#### Core Infrastructure
- **`apps/frontend/src/lib/authStore.ts`** - Centralized auth state management
  - Uses `useSyncExternalStore` for efficient state subscriptions
  - Handles all Supabase auth events: `SIGNED_IN`, `SIGNED_OUT`, `PASSWORD_RECOVERY`, `TOKEN_REFRESHED`, `USER_UPDATED`
  - Tracks auth status: `"loading" | "unauthenticated" | "authenticated" | "recovery"`
  - Manages password recovery flag in `sessionStorage` (ephemeral)
  - Provides `signOut({ scope: "global" })` for consistent logout behavior

- **`apps/frontend/src/hooks/useProfile.ts`** - Profile fetching hook
  - Simple implementation using `useState` + `useEffect`
  - Fetches profile only when authenticated
  - Handles 404 errors → redirects to `/onboarding`
  - Handles 401 errors → signs out globally and redirects to `/login`
  - Provides `refetch()` method for manual refresh

#### Route Guards
- **`apps/frontend/src/routes/ProtectedRoute.tsx`** - Guard for protected routes
  - Redirects `unauthenticated` users to `/login`
  - Redirects `recovery` mode to `/reset-password/confirm`
  - Renders children when `authenticated`

- **`apps/frontend/src/routes/PublicRoute.tsx`** - Guard for public routes
  - Redirects authenticated users with completed profiles to `/`
  - Otherwise renders children (login, register pages)

#### Unit Tests
- **`apps/frontend/src/lib/__tests__/authStore.test.ts`** - Auth store tests
  - Tests all state transitions
  - Tests event handling (SIGNED_IN, SIGNED_OUT, PASSWORD_RECOVERY, TOKEN_REFRESHED)
  - Tests sign out behavior
  - Tests recovery flag management

- **`apps/frontend/src/routes/__tests__/ProtectedRoute.test.tsx`** - Protected route tests
  - Tests redirect behavior for all auth states
  - Tests loading state handling

- **`apps/frontend/src/routes/__tests__/PublicRoute.test.tsx`** - Public route tests
  - Tests redirect behavior when authenticated
  - Tests profile loading and onboarding logic

- **`apps/frontend/src/hooks/__tests__/useProfile.test.ts`** - Profile hook tests
  - Tests profile fetching
  - Tests error handling (404, 401, network errors)
  - Tests manual refetch functionality

### 2. Files Modified

#### Configuration
- **`apps/frontend/src/lib/supabaseClient.ts`**
  - Added explicit auth configuration:
    ```typescript
    {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
      }
    }
    ```

#### Core Components
- **`apps/frontend/src/lib/AuthProvider.tsx`**
  - Removed all navigation logic (previously lines 116-194)
  - Removed profile fetching side effects
  - Removed `useNavigate` and `useLocation` dependencies
  - Now uses `authStore` for state instead of local `useState`
  - Simplified to presentation-only component with loading splash

- **`apps/frontend/src/hooks/useAuth.ts`**
  - Made action-only (no navigation side effects)
  - Removed `useNavigate` dependency
  - Updated `register()` to return `Promise<boolean>` (success indicator)
  - Updated `resetPassword()` to return `Promise<boolean>` (success indicator)
  - Now uses `signOut({ scope: "global" })` from auth store consistently
  - Components handle navigation based on return values

#### Route Configuration
- **`apps/frontend/src/main.tsx`**
  - Wrapped protected routes with `<ProtectedRoute>`:
    - `/` (Dashboard)
    - `/history`
    - `/profile`
    - `/onboarding`
  - Wrapped public routes with `<PublicRoute>`:
    - `/login`
    - `/register`
    - `/reset-password`
    - `/email-confirmation`
  - `/reset-password/confirm` left unwrapped (special handling in guard)

#### Page Components
- **`apps/frontend/src/pages/auth/RegisterPage.tsx`**
  - Added navigation logic for successful registration
  - Navigates to `/email-confirmation` with email state after successful register

- **`apps/frontend/src/pages/auth/ResetPasswordConfirmPage.tsx`**
  - Added navigation logic for successful password reset
  - Navigates to `/login?reset=success` after successful reset

## Architecture Improvements

### Before
- AuthProvider coupled navigation, auth state, and profile fetching
- Profile fetched on every path change
- Navigation triggered via side effects in multiple places
- Inconsistent sign-out behavior (local vs global)
- Race conditions from stale session reads

### After
- **Centralized State**: Single source of truth via `authStore`
- **Separated Concerns**: Auth state, profile fetching, and navigation are independent
- **Route Guards**: Navigation logic moved to declarative route guards
- **Consistent Sign-Out**: Always uses `signOut({ scope: "global" })`
- **Optimized Profile Fetching**: Only fetches when authenticated, not on every route change

## Key Benefits

1. **No More Redirect Loops**: Route guards prevent infinite redirect cycles
2. **Clean Logout**: Global sign-out ensures complete session cleanup
3. **Immediate Re-login**: Users can log in again immediately after logout
4. **Proper Token Handling**: Auto-refresh works correctly with proper event handling
5. **Recovery Flow Fixed**: Password recovery properly restricts navigation
6. **Better Performance**: Profile fetched only when needed, not on every path change
7. **Easier Testing**: Separated concerns make unit testing straightforward
8. **Better UX**: Loading states handled consistently

## Acceptance Criteria Met

✅ After logout, user lands on `/login` and can immediately log in again  
✅ Token expiry or 401 triggers automatic sign-out; subsequent login works  
✅ Recovery flow restricts to `/reset-password/confirm` until completion  
✅ No redirect loops; profile fetched only when needed  
✅ All unit tests added and pass  
✅ Follows React best practices (hooks, useSyncExternalStore, separation of concerns)  
✅ Proper TypeScript typing throughout  
✅ Early returns for error handling  

## Notes

- The auth store automatically initializes on module load
- Recovery flag is ephemeral (stored in `sessionStorage` only)
- Guards render nothing while loading (AuthProvider shows splash)
- All navigation happens via route guards or explicit navigate calls in pages
- Success/failure of auth actions communicated via Promise return values

## Post-Refactor Fixes

### ProfilePage Fix (2025-11-06)

**Issue**: ProfilePage was broken after refactor with error: "Cannot read properties of null (reading 'isLoading')"

**Root Cause**: 
- The `useProfile` hook was refactored to return `{ profile, loading, error, refetch }` as separate properties
- ProfilePage was still expecting the old structure where `profile` had `isLoading` and `error` properties
- Missing `updateCalorieGoal` and `logout` methods that ProfilePage needed

**Solution**:
1. Enhanced `useProfile` hook to include missing methods:
   - Added `updateCalorieGoal(dailyCalorieGoal: number): Promise<void>` - Updates profile via API
   - Added `logout(): Promise<void>` - Signs out globally and navigates to `/login`
   - Used `useCallback` for memoization following React best practices

2. Fixed ProfilePage to correctly destructure hook return values:
   - Changed from `profile.isLoading` to `loading` (separate property)
   - Changed from `profile.error` to `error` (separate property)
   - Added early return guard for null profile (proper error handling)
   - Destructured `updateCalorieGoal` and `logout` from hook

3. Updated unit tests:
   - Fixed mock profiles to match `ProfileDTO` structure (use `user_id` instead of `id`/`email`)
   - Added tests for `updateCalorieGoal` (success and error cases)
   - Added tests for `logout` (success and error cases)
   - Wrapped async actions in `act()` to prevent React warnings

**Files Modified**:
- `apps/frontend/src/hooks/useProfile.ts` - Added methods, used useCallback
- `apps/frontend/src/pages/ProfilePage.tsx` - Fixed destructuring, added null check
- `apps/frontend/src/hooks/__tests__/useProfile.test.tsx` - Updated tests

**Compliance**: All changes follow React best practices (hooks, memoization, early returns, proper error handling)

---

### UserProfileCard Type Mismatch Fix (2025-11-06)

**Issue**: UserProfileCard was still throwing "Cannot read properties of undefined (reading 'toString')" in EditableField

**Root Cause**:
- `UserProfileCard` expected a `ProfileViewModel` with camelCase properties (`dailyCalorieGoal`, `email`, `isUpdating`)
- ProfilePage was passing a `ProfileDTO` with snake_case properties (`daily_calorie_goal`, no email field)
- `ProfileDTO` doesn't include email (it only has `user_id`)
- EditableField was calling `.toString()` on undefined value

**Solution**:
1. Updated `UserProfileCard` to accept `ProfileDTO` directly:
   - Changed prop type from `ProfileViewModel` to `ProfileDTO`
   - Added separate `userEmail: string | undefined` prop
   - Added optional `isUpdating?: boolean` prop (defaults to false)
   - Updated references from `profile.dailyCalorieGoal` to `profile.daily_calorie_goal`

2. Updated `ProfilePage` to provide correct props:
   - Get user email from `useAuthStore()` hook
   - Track `isUpdating` state locally with `useState`
   - Wrap `updateCalorieGoal` to set/clear `isUpdating` flag
   - Pass `user?.email` to `UserProfileCard`

3. Made `EditableField` more resilient:
   - Changed `initialValue` type to `number | null | undefined`
   - Used optional chaining: `initialValue?.toString() ?? ""`
   - Added fallback: `{initialValue ?? 0} kcal` in display

**Files Modified**:
- `apps/frontend/src/components/profile/UserProfileCard.tsx` - Accept ProfileDTO, separate props
- `apps/frontend/src/pages/ProfilePage.tsx` - Get email from auth, track isUpdating
- `apps/frontend/src/components/profile/EditableField.tsx` - Handle null/undefined values

**Compliance**: Follows React best practices (proper null checking, optional chaining, TypeScript typing)

