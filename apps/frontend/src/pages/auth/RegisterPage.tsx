import { AuthForm } from "@/components/auth/AuthForm";
import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { useAuth } from "@/hooks/useAuth";
import { useAuthContext } from "@/lib/AuthProvider";
import { useNavigate } from "react-router-dom";

export function RegisterPage() {
  const { register, isLoading, apiError } = useAuth();
  const { session } = useAuthContext();
  const navigate = useNavigate();

  if (session) {
    return null;
  }

  const handleRegister = async (data: { email: string; password: string }) => {
    const success = await register(data);
    if (success) {
      // Navigate to email confirmation page on success
      navigate("/email-confirmation", { state: { email: data.email } });
    }
  };

  return (
    <AuthPageLayout>
      <AuthForm
        mode="register"
        onSubmit={(data) => { void handleRegister(data); }}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}
