import { AuthForm } from "@/components/auth/AuthForm";
import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { useAuth } from "@/hooks/useAuth";
import { useAuthContext } from "@/lib/AuthProvider";

export function LoginPage() {
  const { login, isLoading, apiError } = useAuth();
  const { session } = useAuthContext();

  // If user is already logged in, AuthProvider will redirect them.
  // This prevents the form from flashing while redirect is happening.
  if (session) {
    return null;
  }

  return (
    <AuthPageLayout>
      <AuthForm
        mode="login"
        onSubmit={login}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}
