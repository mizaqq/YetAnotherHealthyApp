import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { ResetPasswordRequestForm } from "@/components/auth/ResetPasswordRequestForm";
import { type ResetPasswordRequestFormData } from "@/types";
import { useAuth } from "@/hooks/useAuth";

export function ResetPasswordRequestPage(): JSX.Element {
  const { requestPasswordReset, isLoading, apiError } = useAuth();

  const handleSubmit = async (data: ResetPasswordRequestFormData) => {
    await requestPasswordReset(data);
  };

  return (
    <AuthPageLayout>
      <ResetPasswordRequestForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}

