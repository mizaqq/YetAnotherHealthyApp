import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { type AuthFormData } from "@/types";

const mapSupabaseErrorToMessage = (error: any): string => {
  const message = error?.message || "";

  switch (message) {
    case "Invalid login credentials":
      return "Nieprawidłowy email lub hasło.";
    case "Email not confirmed":
      return "Adres email nie został potwierdzony. Sprawdź swoją skrzynkę pocztową.";
    default:
      return "Wystąpił nieoczekiwany błąd.";
  }
};

export function useAuth() {
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const login = async (data: AuthFormData) => {
    setIsLoading(true);
    setApiError(null);
    try {
      const { error } = await supabase.auth.signInWithPassword({ 
        email: data.email, 
        password: data.password 
      });
      if (error) {
        setApiError(mapSupabaseErrorToMessage(error));
      }
      // Success will be handled by onAuthStateChange listener
    } catch (error) {
      setApiError("Wystąpił nieoczekiwany błąd.");
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: AuthFormData) => {
    setIsLoading(true);
    setApiError(null);
    try {
      // TODO: Implement backend registration endpoint
      // await api.register({ email: data.email, password: data.password });
      setApiError("Rejestracja będzie wkrótce dostępna.");
    } catch (error) {
      setApiError("Wystąpił nieoczekiwany błąd.");
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    apiError,
    login,
    register,
  };
}
