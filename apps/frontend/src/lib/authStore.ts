import { useSyncExternalStore } from "react";
import { supabase } from "./supabaseClient";
import type { Session, User, AuthChangeEvent } from "@supabase/supabase-js";

// Auth status types
export type AuthStatus = "loading" | "unauthenticated" | "authenticated" | "recovery";

// Store state type
export type AuthState = {
  status: AuthStatus;
  session: Session | null;
  user: User | null;
  isAuthenticated: boolean;
  isRecovery: boolean;
};

// Storage key for recovery flag
const RECOVERY_FLAG_KEY = "yah:is-password-recovery";

// Internal store state
let currentState: AuthState = {
  status: "loading",
  session: null,
  user: null,
  isAuthenticated: false,
  isRecovery: false,
};

// Subscribers to state changes
let listeners: (() => void)[] = [];

// Helper to check if recovery flag is set
function getRecoveryFlag(): boolean {
  try {
    return sessionStorage.getItem(RECOVERY_FLAG_KEY) === "1";
  } catch {
    return false;
  }
}

// Helper to set recovery flag
function setRecoveryFlag(value: boolean): void {
  try {
    if (value) {
      sessionStorage.setItem(RECOVERY_FLAG_KEY, "1");
    } else {
      sessionStorage.removeItem(RECOVERY_FLAG_KEY);
    }
  } catch {
    // Ignore storage errors
  }
}

// Update state and notify listeners
function updateState(newState: Partial<AuthState>): void {
  currentState = { ...currentState, ...newState };
  listeners.forEach((listener) => listener());
}

// Derive computed properties from session
function computeAuthState(session: Session | null, isRecovery: boolean): AuthState {
  if (isRecovery && session) {
    return {
      status: "recovery",
      session,
      user: session.user,
      isAuthenticated: false, // Recovery session doesn't grant app access
      isRecovery: true,
    };
  }

  if (session) {
    return {
      status: "authenticated",
      session,
      user: session.user,
      isAuthenticated: true,
      isRecovery: false,
    };
  }

  return {
    status: "unauthenticated",
    session: null,
    user: null,
    isAuthenticated: false,
    isRecovery: false,
  };
}

// Handle auth state changes from Supabase
function handleAuthChange(event: AuthChangeEvent, session: Session | null): void {
  console.log("Auth store: handling event", event, session ? "session exists" : "no session");

  // Handle PASSWORD_RECOVERY event
  if (event === "PASSWORD_RECOVERY") {
    setRecoveryFlag(true);
    updateState(computeAuthState(session, true));
    return;
  }

  // Handle SIGNED_OUT event
  if (event === "SIGNED_OUT") {
    setRecoveryFlag(false);
    updateState(computeAuthState(null, false));
    return;
  }

  // Handle SIGNED_IN, TOKEN_REFRESHED, USER_UPDATED
  // Check if we're in recovery mode (shouldn't be for these events)
  const isRecovery = getRecoveryFlag();
  updateState(computeAuthState(session, isRecovery));
}

// Initialize the store
let isInitialized = false;

async function initializeStore(): Promise<void> {
  if (isInitialized) return;
  isInitialized = true;

  // Check for recovery flag on initial load
  const persistedRecovery = getRecoveryFlag();

  // Check URL hash for recovery type
  const hashParams = new URLSearchParams(window.location.hash.substring(1));
  const type = hashParams.get("type");
  const isRecoveryFromUrl = type === "recovery";

  if (isRecoveryFromUrl) {
    setRecoveryFlag(true);
  }

  // Get initial session
  try {
    const { data: { session } } = await supabase.auth.getSession();
    const isRecovery = isRecoveryFromUrl || persistedRecovery;
    
    updateState(computeAuthState(session, isRecovery));

    // Clean up URL hash if recovery
    if (isRecoveryFromUrl && window.location.hash) {
      window.history.replaceState(null, "", window.location.pathname + window.location.search);
    }
  } catch (error) {
    console.error("Error getting initial session:", error);
    updateState({ status: "unauthenticated", session: null, user: null });
  }

  // Subscribe to auth changes
  supabase.auth.onAuthStateChange((event, session) => {
    handleAuthChange(event, session);
  });
}

// Start initialization immediately
void initializeStore();

// Subscribe function for useSyncExternalStore
function subscribe(listener: () => void): () => void {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

// Get snapshot function for useSyncExternalStore
function getSnapshot(): AuthState {
  return currentState;
}

// Hook to access auth state
export function useAuthStore(): AuthState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

// Action to sign out
export async function signOut(options?: { scope?: "local" | "global" }): Promise<void> {
  const scope = options?.scope ?? "global";
  
  try {
    await supabase.auth.signOut({ scope });
    // Clear recovery flag
    setRecoveryFlag(false);
    // Update state immediately
    updateState(computeAuthState(null, false));
  } catch (error) {
    console.error("Error signing out:", error);
    // Still clear local state even if API call fails
    setRecoveryFlag(false);
    updateState(computeAuthState(null, false));
  }
}

// Action to refresh session
export async function refreshSession(): Promise<void> {
  try {
    const { data: { session }, error } = await supabase.auth.refreshSession();
    if (error) throw error;
    
    const isRecovery = getRecoveryFlag();
    updateState(computeAuthState(session, isRecovery));
  } catch (error) {
    console.error("Error refreshing session:", error);
    // If refresh fails, sign out
    await signOut({ scope: "global" });
  }
}

// Action to clear recovery flag (used after successful password reset)
export function clearPasswordRecovery(): void {
  setRecoveryFlag(false);
  // Recompute state without recovery
  const isRecovery = false;
  updateState(computeAuthState(currentState.session, isRecovery));
}

