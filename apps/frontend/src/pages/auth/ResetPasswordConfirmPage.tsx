import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { ResetPasswordConfirmForm } from "@/components/auth/ResetPasswordConfirmForm";
import { type ResetPasswordConfirmFormData } from "@/types";
import { useAuth } from "@/hooks/useAuth";
import { useAuthContext } from "@/lib/AuthProvider";

export function ResetPasswordConfirmPage(): JSX.Element {
  const { resetPassword, isLoading, apiError } = useAuth();
  const { isPasswordRecovery } = useAuthContext();

  const handleSubmit = async (data: ResetPasswordConfirmFormData) => {
    await resetPassword(data);
  };

  // Show error if not in password recovery mode
  if (!isPasswordRecovery) {
    return (
      <AuthPageLayout>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '24px',
          textAlign: 'center'
        }}>
          <h2 style={{ marginBottom: '16px' }}>Nieprawidłowy link resetowania hasła</h2>
          <p style={{ color: '#666', marginBottom: '24px' }}>
            Link resetowania hasła jest nieprawidłowy lub wygasł. Spróbuj ponownie poprosić o reset hasła.
          </p>
          <button
            onClick={() => window.location.href = '/reset-password'}
            style={{
              padding: '12px 24px',
              backgroundColor: '#0078d4',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Poproś o nowy link
          </button>
        </div>
      </AuthPageLayout>
    );
  }

  return (
    <AuthPageLayout>
      <ResetPasswordConfirmForm
        onSubmit={handleSubmit}
        isLoading={isLoading}
        apiError={apiError}
      />
    </AuthPageLayout>
  );
}

