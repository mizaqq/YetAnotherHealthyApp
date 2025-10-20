import React, { createContext, useContext, useEffect, useState } from "react";
import { Session } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabaseClient";
import { useNavigate } from "react-router-dom";
import { getProfile } from "@/lib/api";

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
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Effect to handle navigation based on session state
  useEffect(() => {
    if (loading) return; // Wait until the initial session check is complete

    const handleNavigation = async () => {
      // If user is present, check their profile
      if (session) {
        try {
          const profile = await getProfile();
          // If onboarding is not complete, redirect there
          if (!profile.onboarding_completed_at) {
            if (window.location.pathname !== "/onboarding") {
              navigate("/onboarding", { replace: true });
            }
          }
          // If user is on an auth page after login, redirect to dashboard
          else if (["/login", "/register"].includes(window.location.pathname)) {
            navigate("/", { replace: true });
          }
        } catch (error) {
          console.error("Failed to fetch profile:", error);
          // If profile fetch fails, log the user out to be safe
          await supabase.auth.signOut();
          navigate("/login", { replace: true });
        }
      }
      // If no user session, redirect to login unless already on an auth page
      else {
        if (!["/login", "/register"].includes(window.location.pathname)) {
          navigate("/login", { replace: true });
        }
      }
    };

    handleNavigation();
  }, [session, loading, navigate]);

  return (
    <AuthContext.Provider value={{ session, loading }}>
      {loading ? <div>Loading...</div> : children}
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
