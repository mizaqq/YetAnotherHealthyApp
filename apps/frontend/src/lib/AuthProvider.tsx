import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabaseClient";
import { useNavigate, useLocation } from "react-router-dom";
import { getProfile } from "@/lib/api";

// Auth page paths used for navigation logic
const AUTH_PAGES = ["/login", "/register", "/reset-password", "/reset-password/confirm", "/email-confirmation"];

type AuthContextType = {
  session: Session | null;
  loading: boolean;
  isPasswordRecovery: boolean;
  clearPasswordRecovery: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isPasswordRecovery, setIsPasswordRecovery] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const clearPasswordRecovery = useCallback(() => {
    try {
      sessionStorage.removeItem("yah:is-password-recovery");
    } catch {
      // Ignore storage errors
    }
    setIsPasswordRecovery(false);
  }, []);

  // Effect to handle Supabase auth state changes
  useEffect(() => {
    // Restore recovery mode from session storage on initial load
    try {
      const persistedRecovery = sessionStorage.getItem("yah:is-password-recovery");
      if (persistedRecovery === "1") {
        setIsPasswordRecovery(true);
      }
    } catch {
      // Ignore storage errors
    }

    // Check URL for recovery hash on initial load
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const type = hashParams.get('type');
    
    if (type === 'recovery') {
      console.log("Password recovery detected from URL hash");
      setIsPasswordRecovery(true);
      try { sessionStorage.setItem("yah:is-password-recovery", "1"); } catch {
        // Ignore storage errors
      }
    }

    // 1. Get the initial session
    supabase.auth
      .getSession()
      .then(({ data: { session } }) => {
        setSession(session);
        
        // If we have a session and it's a recovery flow, navigate to confirm page
        if (session && type === 'recovery') {
          // Strip hash AFTER session is created and before navigation
          window.history.replaceState(null, "", window.location.pathname + window.location.search);
          navigate("/reset-password/confirm", { replace: true });
        }
      })
      .catch((error) => {
        console.error("Error getting session:", error);
      })
      .finally(() => {
        setLoading(false); // Crucially, unblock the UI regardless of outcome
      });

    // 2. Listen for future changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      // Auth state logging for debugging authentication flows
      console.log("Auth state change:", event, session ? "session exists" : "no session");
      
      // Handle password recovery flow
      if (event === "PASSWORD_RECOVERY") {
        setIsPasswordRecovery(true);
        try {
          sessionStorage.setItem("yah:is-password-recovery", "1");
        } catch {
          // Ignore storage errors
        }
        // Strip hash before navigating to confirm page
        if (window.location.hash) {
          window.history.replaceState(null, "", window.location.pathname + window.location.search);
        }
        navigate("/reset-password/confirm", { replace: true });
      }
      
      // Clear recovery flag on sign out
      if (event === "SIGNED_OUT") {
        try { sessionStorage.removeItem("yah:is-password-recovery"); } catch {
          // Ignore storage errors
        }
        setIsPasswordRecovery(false);
      }
      
      setSession(session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [navigate]);

  // Effect to handle navigation based on session state
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

        // Guard: Redirect to onboarding if not completed
        if (!profile.onboarding_completed_at) {
          if (location.pathname !== "/onboarding") {
            navigate("/onboarding", { replace: true });
          }
          return;
        }

        // Guard: Redirect authenticated users away from auth pages
        if (AUTH_PAGES.includes(location.pathname)) {
          navigate("/", { replace: true });
        }
      } catch (error) {
        console.error("Failed to fetch profile:", error);

        // Handle profile not found (404) - new users need onboarding
        const isNotFoundError =
          error instanceof Error &&
          (error.message.toLowerCase().includes("not found") ||
            error.message.toLowerCase().includes("404"));

        if (isNotFoundError) {
          if (location.pathname !== "/onboarding") {
            navigate("/onboarding", { replace: true });
          }
          return;
        }

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
      }
    };

    void handleNavigation();
  }, [loading, session, navigate, isPasswordRecovery, location.pathname]);

  return (
    <AuthContext.Provider value={{ session, loading, isPasswordRecovery, clearPasswordRecovery }}>
      {loading ? (
        <div
          role="status"
          aria-live="polite"
          aria-label="Ładowanie aplikacji"
          className="flex items-center justify-center min-h-screen"
        >
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Ładowanie...</p>
          </div>
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuthContext must be used within an AuthProvider");
  }
  return context;
};
