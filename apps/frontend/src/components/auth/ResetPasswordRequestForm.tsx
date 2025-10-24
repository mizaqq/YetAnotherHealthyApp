import {
  Card,
  CardHeader,
  Button,
  Input,
  Label,
  Text,
  makeStyles,
  shorthands,
  tokens,
  Spinner,
} from "@fluentui/react-components";
import {
  type ResetPasswordRequestFormProps,
  type ResetPasswordRequestFormData,
} from "@/types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";

const resetPasswordRequestSchema = z.object({
  email: z.string().trim().email({ message: "Nieprawidłowy adres email." }),
});

const useStyles = makeStyles({
  card: {
    width: "100%",
    maxWidth: "420px",
    ...shorthands.margin("auto"),
    ...shorthands.padding("24px"),
  },
  form: {
    display: "grid",
    width: "100%",
    alignItems: "center",
    ...shorthands.gap("24px"),
  },
  field: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("4px"),
  },
  errorText: {
    color: tokens.colorPaletteRedForeground1,
    fontWeight: tokens.fontWeightMedium,
  },
  successContainer: {
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorPaletteGreenBackground1,
    ...shorthands.padding("16px"),
    ...shorthands.border("1px", "solid", tokens.colorPaletteGreenBorder1),
  },
  successText: {
    color: tokens.colorPaletteGreenForeground1,
    fontWeight: tokens.fontWeightMedium,
  },
  apiErrorContainer: {
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    backgroundColor: tokens.colorPaletteRedBackground1,
    ...shorthands.padding("16px"),
    ...shorthands.border("1px", "solid", tokens.colorPaletteRedBorder1),
  },
  footer: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("20px"),
    paddingTop: "16px",
  },
});

export function ResetPasswordRequestForm({
  onSubmit,
  isLoading,
  apiError,
}: ResetPasswordRequestFormProps): JSX.Element {
  const styles = useStyles();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors, isValid, isSubmitSuccessful },
  } = useForm<ResetPasswordRequestFormData>({
    resolver: zodResolver(resetPasswordRequestSchema),
    mode: "onChange",
  });

  const handleFormSubmit = async (data: ResetPasswordRequestFormData) => {
    await onSubmit(data);
  };

  return (
    <Card className={styles.card}>
      <CardHeader
        header={
          <Text size={700} weight="bold">
            Resetuj hasło
          </Text>
        }
        description={
          <Text size={400}>
            Podaj adres email powiązany z Twoim kontem. Wyślemy Ci link do
            resetowania hasła.
          </Text>
        }
      />
      <form
        onSubmit={handleSubmit(handleFormSubmit)}
        id="reset-password-request-form"
        className={styles.form}
      >
        {isSubmitSuccessful && !apiError ? (
          <div
            className={styles.successContainer}
            role="status"
            aria-live="polite"
          >
            <Text id="success-message" className={styles.successText}>
              Jeśli konto z tym adresem email istnieje, wyślemy link do
              resetowania hasła. Sprawdź swoją skrzynkę pocztową.
            </Text>
          </div>
        ) : (
          <>
            <div className={styles.field}>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                {...register("email")}
                aria-invalid={errors.email ? "true" : "false"}
                aria-describedby={errors.email ? "email-error" : undefined}
              />
              {errors.email && (
                <Text id="email-error" className={styles.errorText}>
                  {errors.email.message}
                </Text>
              )}
            </div>
            {apiError && (
              <div
                className={styles.apiErrorContainer}
                role="alert"
                aria-live="polite"
              >
                <Text id="api-error" className={styles.errorText}>
                  {apiError}
                </Text>
              </div>
            )}
          </>
        )}
        <div className={styles.footer}>
          {!isSubmitSuccessful && (
            <Button
              type="submit"
              form="reset-password-request-form"
              appearance="primary"
              size="large"
              style={{ width: "100%" }}
              disabled={isLoading || !isValid}
              data-testid="reset-password-request-submit"
            >
              {isLoading ? (
                <>
                  <Spinner size="tiny" />
                  <span style={{ marginLeft: "8px" }}>Wysyłanie...</span>
                </>
              ) : (
                "Wyślij link"
              )}
            </Button>
          )}
          <Text style={{ textAlign: "center" }}>
            Pamiętasz hasło?{" "}
            <Button
              type="button"
              appearance="subtle"
              onClick={() => navigate("/login")}
            >
              Zaloguj się
            </Button>
          </Text>
        </div>
      </form>
    </Card>
  );
}

