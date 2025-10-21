import { OnboardingForm } from "@/components/onboarding/OnboardingForm";
import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { useOnboarding } from "@/hooks/useOnboarding";
import { useAuthContext } from "@/lib/AuthProvider";

export function OnboardingPage() {
  const { submitOnboarding, isLoading, apiError } = useOnboarding();
  const { session } = useAuthContext();

  // If user is not logged in, AuthProvider will redirect them.
  // This prevents the form from flashing while redirect is happening.
  if (!session) {
    return null;
  }

  return (
    <AuthPageLayout>
      <OnboardingForm
        onSubmit={submitOnboarding}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}


