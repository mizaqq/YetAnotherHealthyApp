import { useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { clearPasswordRecovery, signOut } from "@/lib/authStore";
import { 
  postAuthRegister, 
  postAuthPasswordResetRequest, 
  postAuthPasswordResetConfirm 
} from "@/lib/api";
import { type AuthFormData, type ResetPasswordRequestFormData, type ResetPasswordConfirmFormData } from "@/types";

const mapSupabaseErrorToMessage = (error: unknown): string => {
  if (!error || typeof error !== 'object') {
    return "Wystąpił nieoczekiwany błąd.";
  }
  
  const message = 'message' in error && typeof error.message === 'string' ? error.message : "";

  switch (message) {
    case "Invalid login credentials":
      return "Nieprawidłowy email lub hasło.";
    case "Email not confirmed":
      return "Adres email nie został potwierdzony. Sprawdź swoją skrzynkę pocztową.";
    default:
      return "Wystąpił nieoczekiwany błąd.";
  }
};

const mapApiErrorToMessage = (error: unknown): string => {
  if (!error || typeof error !== 'object') {
    return "Wystąpił nieoczekiwany błąd.";
  }
  
  const message = 'message' in error && typeof error.message === 'string' ? error.message : "";

  // Handle 409 Conflict for duplicate email
  if (message.includes("Conflict")) {
    return "Adres email jest już zajęty.";
  }

  // Handle 401 Unauthorized for invalid/expired recovery token
  if (message.includes("Unauthorized")) {
    return "Link resetowania nieprawidłowy lub wygasł.";
  }

  return "Wystąpił nieoczekiwany błąd.";
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
    } catch {
      setApiError("Wystąpił nieoczekiwany błąd.");
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: AuthFormData): Promise<boolean> => {
    setIsLoading(true);
    setApiError(null);
    try {
      await postAuthRegister({ email: data.email, password: data.password });
      // Success - component will handle navigation
      return true;
    } catch (error) {
      setApiError(mapApiErrorToMessage(error));
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const requestPasswordReset = async (data: ResetPasswordRequestFormData) => {
    setIsLoading(true);
    setApiError(null);
    try {
      await postAuthPasswordResetRequest({ email: data.email });
      // Always show success - security measure to not reveal email existence
      // The component handles showing success state via isSubmitSuccessful
    } catch (error) {
      // Even on error, we don't show anything to the user for security
      // The backend always returns 202 Accepted
      console.error("Password reset request error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async (data: ResetPasswordConfirmFormData): Promise<boolean> => {
    setIsLoading(true);
    setApiError(null);
    try {
      await postAuthPasswordResetConfirm({ password: data.password });
      // Clear password recovery flag immediately
      clearPasswordRecovery();
      
      // Sign out globally (removes session from server)
      await signOut({ scope: "global" });
      
      // Success - component will handle navigation to /login?reset=success
      return true;
    } catch (error) {
      setApiError(mapApiErrorToMessage(error));
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    apiError,
    login,
    register,
    requestPasswordReset,
    resetPassword,
  };
}
