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
import { type AuthFormProps, type AuthFormData } from "@/types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Link, useNavigate } from "react-router-dom";
import { EyeRegular, EyeOffRegular } from "@fluentui/react-icons";
import { useState } from "react";

// TODO: Implement password validation
const loginSchema = z.object({
  email: z.string().email({ message: "Nieprawidłowy adres email." }),
  password: z.string().min(1, { message: "Hasło jest wymagane." }),
});

const registerSchema = z.object({
  email: z.string().email({ message: "Nieprawidłowy adres email." }),
  password: z
    .string()
    .min(8, { message: "Hasło musi mieć co najmniej 8 znaków." })
    .regex(/[a-zA-Z]/, {
      message: "Hasło musi zawierać co najmniej jedną literę.",
    })
    .regex(/[0-9]/, { message: "Hasło musi zawierać co najmniej jedną cyfrę." }),
});

const formContent = {
  login: {
    title: "Witaj z powrotem!",
    description: "Zaloguj się, aby kontynuować.",
    buttonText: "Zaloguj się",
    footerText: "Nie masz jeszcze konta?",
    footerLinkText: "Zarejestruj się",
    footerTo: "/register",
  },
  register: {
    title: "Stwórz konto",
    description: "Dołącz do nas i zacznij śledzić swoje postępy.",
    buttonText: "Zarejestruj się",
    footerText: "Masz już konto?",
    footerLinkText: "Zaloguj się",
    footerTo: "/login",
  },
};

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
  passwordInput: {
    paddingRight: "40px",
  },
  passwordToggle: {
    position: "absolute",
    right: "0px",
    top: "0px",
    height: "100%",
    paddingLeft: "12px",
    paddingRight: "12px",
  },
  errorText: {
    color: tokens.colorPaletteRedForeground1,
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

export function AuthForm({
  mode,
  onSubmit,
  isLoading,
  apiError,
}: AuthFormProps): JSX.Element {
  const styles = useStyles();
  const content = formContent[mode];
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<AuthFormData>({
    resolver: zodResolver(mode === "login" ? loginSchema : registerSchema),
    mode: "onChange",
  });

  const handleFormSubmit = async (data: AuthFormData) => {
    await onSubmit(data);
    // Navigation will be handled by AuthProvider's onAuthStateChange
  };

  return (
    <Card className={styles.card}>
      <CardHeader
        header={<Text size={700} weight="bold">{content.title}</Text>}
        description={<Text size={400}>{content.description}</Text>}
      />
      <form onSubmit={handleSubmit(handleFormSubmit)} id="auth-form" className={styles.form}>
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
        <div className={styles.field}>
          <Label htmlFor="password">Hasło</Label>
          <div style={{ position: "relative" }}>
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              contentAfter={
                <Button
                  appearance="transparent"
                  className={styles.passwordToggle}
                  onClick={() => setShowPassword(!showPassword)}
                  icon={showPassword ? <EyeOffRegular /> : <EyeRegular />}
                  aria-label={showPassword ? "Ukryj hasło" : "Pokaż hasło"}
                  tabIndex={-1}
                />
              }
              {...register("password")}
              aria-invalid={errors.password ? "true" : "false"}
              aria-describedby={
                errors.password ? "password-error" : undefined
              }
            />
          </div>
          {errors.password && (
            <Text id="password-error" className={styles.errorText}>
              {errors.password.message}
            </Text>
          )}
        </div>
        {apiError && (
          <div className={styles.apiErrorContainer} role="alert" aria-live="polite">
            <Text id="api-error" className={styles.errorText}>
              {apiError}
            </Text>
          </div>
        )}
        <div className={styles.footer}>
          <Button
            type="submit"
            form="auth-form"
            appearance="primary"
            size="large"
            style={{ width: "100%" }}
            disabled={isLoading || !isValid}
            data-testid="auth-submit"
          >
            {isLoading ? (
              <>
                <Spinner size="tiny" />
                <span style={{ marginLeft: '8px' }}>Przetwarzanie...</span>
              </>
            ) : (
              content.buttonText
            )}
          </Button>
          <Text style={{ textAlign: "center" }}>
            {content.footerText}{" "}
            <Button
              appearance="subtle"
              onClick={() => navigate(content.footerTo)}
            >
              {content.footerLinkText}
            </Button>
          </Text>
        </div>
      </form>
    </Card>
  );
}
