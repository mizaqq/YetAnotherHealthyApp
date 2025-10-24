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
  type ResetPasswordConfirmFormProps,
  type ResetPasswordConfirmFormData,
} from "@/types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { EyeRegular, EyeOffRegular } from "@fluentui/react-icons";
import { useState } from "react";

const resetPasswordConfirmSchema = z
  .object({
    password: z
      .string()
      .trim()
      .min(8, { message: "Hasło musi mieć co najmniej 8 znaków." })
      .regex(/[a-zA-Z]/, {
        message: "Hasło musi zawierać co najmniej jedną literę.",
      })
      .regex(/[0-9]/, {
        message: "Hasło musi zawierać co najmniej jedną cyfrę.",
      }),
    confirmPassword: z.string().trim(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Hasła muszą być identyczne.",
    path: ["confirmPassword"],
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

export function ResetPasswordConfirmForm({
  onSubmit,
  isLoading,
  apiError,
}: ResetPasswordConfirmFormProps): JSX.Element {
  const styles = useStyles();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<ResetPasswordConfirmFormData>({
    resolver: zodResolver(resetPasswordConfirmSchema),
    mode: "onChange",
  });

  const handleFormSubmit = async (data: ResetPasswordConfirmFormData) => {
    await onSubmit(data);
  };

  return (
    <Card className={styles.card}>
      <CardHeader
        header={
          <Text size={700} weight="bold">
            Ustaw nowe hasło
          </Text>
        }
        description={
          <Text size={400}>
            Wprowadź nowe hasło dla swojego konta. Hasło musi mieć co najmniej
            8 znaków i zawierać literę oraz cyfrę.
          </Text>
        }
      />
      <form
        onSubmit={handleSubmit(handleFormSubmit)}
        id="reset-password-confirm-form"
        className={styles.form}
      >
        <div className={styles.field}>
          <Label htmlFor="password">Nowe hasło</Label>
          <div style={{ position: "relative" }}>
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              contentAfter={
                <Button
                  type="button"
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
              aria-describedby={errors.password ? "password-error" : undefined}
            />
          </div>
          {errors.password && (
            <Text id="password-error" className={styles.errorText}>
              {errors.password.message}
            </Text>
          )}
        </div>
        <div className={styles.field}>
          <Label htmlFor="confirmPassword">Potwierdź nowe hasło</Label>
          <div style={{ position: "relative" }}>
            <Input
              id="confirmPassword"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              contentAfter={
                <Button
                  type="button"
                  appearance="transparent"
                  className={styles.passwordToggle}
                  onClick={() =>
                    setShowConfirmPassword(!showConfirmPassword)
                  }
                  icon={
                    showConfirmPassword ? <EyeOffRegular /> : <EyeRegular />
                  }
                  aria-label={
                    showConfirmPassword ? "Ukryj hasło" : "Pokaż hasło"
                  }
                  tabIndex={-1}
                />
              }
              {...register("confirmPassword")}
              aria-invalid={errors.confirmPassword ? "true" : "false"}
              aria-describedby={
                errors.confirmPassword ? "confirm-password-error" : undefined
              }
            />
          </div>
          {errors.confirmPassword && (
            <Text id="confirm-password-error" className={styles.errorText}>
              {errors.confirmPassword.message}
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
        <div className={styles.footer}>
          <Button
            type="submit"
            form="reset-password-confirm-form"
            appearance="primary"
            size="large"
            style={{ width: "100%" }}
            disabled={isLoading || !isValid}
            data-testid="reset-password-confirm-submit"
          >
            {isLoading ? (
              <>
                <Spinner size="tiny" />
                <span style={{ marginLeft: "8px" }}>Resetowanie...</span>
              </>
            ) : (
              "Ustaw nowe hasło"
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}

