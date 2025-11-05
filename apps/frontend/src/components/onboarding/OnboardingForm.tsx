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
import { type OnboardingFormProps, type CreateOnboardingCommand } from "@/types";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const onboardingSchema = z.object({
  daily_calorie_goal: z.coerce
    .number({ invalid_type_error: "Wartość musi być liczbą." })
    .int({ message: "Wartość musi być liczbą całkowitą." })
    .min(500, { message: "Wartość musi być większa niż 500." }),
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

export function OnboardingForm({
  onSubmit,
  isLoading,
  apiError,
}: OnboardingFormProps): JSX.Element {
  const styles = useStyles();
  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
  } = useForm<CreateOnboardingCommand>({
    resolver: zodResolver(onboardingSchema),
    mode: "onChange",
  });

  const handleFormSubmit = (data: CreateOnboardingCommand) => {
    void onSubmit(data);
  };

  return (
    <Card className={styles.card}>
      <CardHeader
        header={
          <Text size={700} weight="bold">
            Ustaw swój dzienny cel
          </Text>
        }
        description={
          <Text size={400}>
            Podaj swój cel kaloryczny, abyśmy mogli pomóc Ci śledzić postępy.
          </Text>
        }
      />
      <form
        onSubmit={(e) => { void handleSubmit(handleFormSubmit)(e); }}
        id="onboarding-form"
        className={styles.form}
      >
        <div className={styles.field}>
          <Label htmlFor="daily_calorie_goal">Dzienny cel kaloryczny (kcal)</Label>
          <Input
            id="daily_calorie_goal"
            type="number"
            placeholder="np. 2000"
            {...register("daily_calorie_goal")}
            aria-invalid={errors.daily_calorie_goal ? "true" : "false"}
            aria-describedby={
              errors.daily_calorie_goal ? "calorie-goal-error" : undefined
            }
          />
          {errors.daily_calorie_goal && (
            <Text id="calorie-goal-error" className={styles.errorText}>
              {errors.daily_calorie_goal.message}
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
            form="onboarding-form"
            appearance="primary"
            size="large"
            style={{ width: "100%" }}
            disabled={isLoading || !isValid}
            data-testid="onboarding-submit"
          >
            {isLoading ? (
              <>
                <Spinner size="tiny" />
                <span style={{ marginLeft: "8px" }}>Zapisywanie...</span>
              </>
            ) : (
              "Zapisz i kontynuuj"
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
}


