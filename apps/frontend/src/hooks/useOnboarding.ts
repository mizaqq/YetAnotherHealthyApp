import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { completeOnboarding } from "@/lib/api";
import { type CreateOnboardingCommand } from "@/types";

export function useOnboarding() {
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const navigate = useNavigate();

  const submitOnboarding = async (data: CreateOnboardingCommand) => {
    setIsLoading(true);
    setApiError(null);
    
    try {
      await completeOnboarding(data);
      // Success - redirect to dashboard
      navigate("/", { replace: true });
    } catch (error) {
      // Handle 409 Conflict (onboarding already completed)
      if (error instanceof Error && error.message.includes("409")) {
        // Silent redirect - user already completed onboarding
        navigate("/", { replace: true });
        return;
      }
      
      // Handle other errors
      if (error instanceof Error) {
        setApiError(error.message);
      } else {
        setApiError("Wystąpił nieoczekiwany błąd. Spróbuj ponownie później.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    apiError,
    submitOnboarding,
  };
}

