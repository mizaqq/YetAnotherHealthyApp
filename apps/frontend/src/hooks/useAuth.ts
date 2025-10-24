import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabaseClient";
import { useAuthContext } from "@/lib/AuthProvider";
import { 
  postAuthRegister, 
  postAuthPasswordResetRequest, 
  postAuthPasswordResetConfirm 
} from "@/lib/api";
import { type AuthFormData, type ResetPasswordRequestFormData, type ResetPasswordConfirmFormData } from "@/types";

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

const mapApiErrorToMessage = (error: any): string => {
  const message = error?.message || "";

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
  const navigate = useNavigate();
  const { clearPasswordRecovery } = useAuthContext();

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
      await postAuthRegister({ email: data.email, password: data.password });
      // Navigate to email confirmation page on success
      navigate("/email-confirmation", { state: { email: data.email } });
    } catch (error) {
      setApiError(mapApiErrorToMessage(error));
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

  const resetPassword = async (data: ResetPasswordConfirmFormData) => {
    setIsLoading(true);
    setApiError(null);
    try {
      await postAuthPasswordResetConfirm({ password: data.password });
      // Clear password recovery flag immediately
      clearPasswordRecovery();
      
      // Sign out globally (removes session from server) instead of just local
      await supabase.auth.signOut({ scope: "global" });
      
      // Give Supabase a moment to complete the sign-out
      await new Promise(r => setTimeout(r, 100));
      
      // Navigate to login with success flag
      navigate("/login?reset=success", { replace: true });
    } catch (error) {
      setApiError(mapApiErrorToMessage(error));
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
