import { AuthForm } from "@/components/auth/AuthForm";
import { AuthPageLayout } from "@/components/auth/AuthPageLayout";
import { useAuth } from "@/hooks/useAuth";
import { useSearchParams } from "react-router-dom";
import {
  MessageBar,
  MessageBarBody,
  makeStyles,
} from "@fluentui/react-components";

const useStyles = makeStyles({
  successMessage: {
    marginBottom: "24px",
    width: "100%",
    maxWidth: "420px",
  },
});

export function LoginPage() {
  const { login, isLoading, apiError } = useAuth();
  const [searchParams] = useSearchParams();
  const resetSuccess = searchParams.get("reset") === "success";
  const styles = useStyles();

  return (
    <AuthPageLayout>
      <div style={{ width: "100%", maxWidth: "420px", margin: "auto" }}>
        {resetSuccess && (
          <MessageBar intent="success" className={styles.successMessage}>
            <MessageBarBody>
              Hasło zostało zmienione. Zaloguj się przy użyciu nowego hasła.
            </MessageBarBody>
          </MessageBar>
        )}
        <AuthForm
          mode="login"
          onSubmit={login}
          isLoading={isLoading}
          apiError={apiError}
        />
      </div>
    </AuthPageLayout>
  );
}
