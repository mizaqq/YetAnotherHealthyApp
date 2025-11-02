import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { EmailConfirmationView } from "@/components/auth/EmailConfirmationView";
import { useLocation } from "react-router-dom";

export function EmailConfirmationPage(): JSX.Element {
  const location = useLocation();
  const email = 'email' in (location.state ?? {}) ? (location.state as { email: string }).email : undefined;

  return (
    <AuthPageLayout>
      <EmailConfirmationView email={email} />
    </AuthPageLayout>
  );
}

