import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { type AuthFormData } from "@/types";

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleSupabaseAuth = async (
    authFunction: (data: AuthFormData) => Promise<any>,
    data: AuthFormData
  ) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const { error } = await authFunction(data);
      if (error) {
        // TODO: Map Supabase errors to user-friendly messages
        setApiError(error.message);
      }
      // Success will be handled by onAuthStateChange listener
    } catch (error) {
      setApiError("Wystąpił nieoczekiwany błąd.");
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (data: AuthFormData) => {
    await handleSupabaseAuth(
      (d) => supabase.auth.signInWithPassword({ email: d.email, password: d.password }),
      data
    );
  };

  const register = async (data: AuthFormData) => {
    await handleSupabaseAuth(
      (d) => supabase.auth.signUp({ email: d.email, password: d.password }),
      data
    );
  };

  return {
    isLoading,
    apiError,
    login,
    register,
  };
}
