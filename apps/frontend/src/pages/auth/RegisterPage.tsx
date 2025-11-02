import { AuthForm } from "@/components/auth/AuthForm";
import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { useAuth } from "@/hooks/useAuth";
import { useAuthContext } from "@/lib/AuthProvider";

export function RegisterPage() {
  const { register, isLoading, apiError } = useAuth();
  const { session } = useAuthContext();

  if (session) {
    return null;
  }

  return (
    <AuthPageLayout>
      <AuthForm
        mode="register"
        onSubmit={(data) => { void register(data); }}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}
