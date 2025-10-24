import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabaseClient";
import { useNavigate } from "react-router-dom";
import { getProfile } from "@/lib/api";

// Auth page paths used for navigation logic
const AUTH_PAGES = ["/login", "/register"];

type AuthContextType = {
  session: Session | null;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Effect to handle Supabase auth state changes
  useEffect(() => {
    // 1. Get the initial session
    supabase.auth
      .getSession()
      .then(({ data: { session } }) => {
        setSession(session);
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
      setSession(session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Handle navigation based on authentication state
  // Uses guard clauses to reduce nesting and improve readability
  const handleNavigation = useCallback(async (): Promise<void> => {
    // Guard: No session - redirect to login if not on auth page
    if (!session) {
      if (!AUTH_PAGES.includes(window.location.pathname)) {
        navigate("/login", { replace: true });
      }
      return;
    }

    // User has session - check their profile to determine navigation
    try {
      const profile = await getProfile();

      // Guard: Redirect to onboarding if not completed
      if (!profile.onboarding_completed_at) {
        if (window.location.pathname !== "/onboarding") {
          navigate("/onboarding", { replace: true });
        }
        return;
      }

      // Guard: Redirect authenticated users away from auth pages
      if (AUTH_PAGES.includes(window.location.pathname)) {
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
        if (window.location.pathname !== "/onboarding") {
          navigate("/onboarding", { replace: true });
        }
        return;
      }

      // For other errors (unauthorized, network issues), sign out the user
      await supabase.auth.signOut();
      navigate("/login", { replace: true });
    }
  }, [session, navigate]);

  // Effect to handle navigation based on session state
  useEffect(() => {
    if (loading) return; // Wait until the initial session check is complete

    handleNavigation();
  }, [loading, handleNavigation]);

  return (
    <AuthContext.Provider value={{ session, loading }}>
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
