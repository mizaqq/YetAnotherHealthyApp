import { useForm, Controller } from "react-hook-form";
import {
  Button,
  Field,
  Input,
  Textarea,
  Dropdown,
  Option,
  Switch,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import type { MealCategoryDTO, MealInputFormViewModel } from "@/types";

type MealInputStepProps = {
  initialData: Partial<MealInputFormViewModel>;
  categories: MealCategoryDTO[];
  isLoading: boolean;
  onSubmit: (data: MealInputFormViewModel) => void;
};

const useStyles = makeStyles({
  form: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  buttonGroup: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalM),
    justifyContent: "flex-end",
    marginTop: tokens.spacingVerticalL,
  },
});

export function MealInputStep({
  initialData,
  categories,
  isLoading,
  onSubmit,
}: MealInputStepProps) {
  const styles = useStyles();

  const {
    control,
    handleSubmit,
    watch,
    formState: { errors },
    setValue,
    setError,
  } = useForm<MealInputFormViewModel>({
    defaultValues: {
      category: initialData.category ?? "",
      description: initialData.description ?? "",
      isManualMode: initialData.isManualMode ?? false,
      manualCalories: initialData.manualCalories ?? null,
    },
  });

  const isManualMode = watch("isManualMode");

  const handleFormSubmit = (data: MealInputFormViewModel) => {
    // Manual validation based on mode
    let hasErrors = false;

    if (!data.category) {
      setError("category", { message: "Wybierz kategorię posiłku" });
      hasErrors = true;
    }

    if (!data.isManualMode) {
      if (!data.description || data.description.length < 3) {
        setError("description", {
          message: "Opis musi zawierać co najmniej 3 znaki",
        });
        hasErrors = true;
      }
    } else {
      if (!data.manualCalories || data.manualCalories <= 0) {
        setError("manualCalories", {
          message: "Kalorie muszą być większe niż 0",
        });
        hasErrors = true;
      }
    }

    if (!hasErrors) {
      onSubmit(data);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(handleFormSubmit)(e)} className={styles.form}>
      <Controller
        name="category"
        control={control}
        render={({ field }) => (
          <Field
            label="Kategoria posiłku"
            required
            validationMessage={errors.category?.message}
            validationState={errors.category ? "error" : "none"}
          >
            <Dropdown
              {...field}
              value={
                categories.find((c) => c.code === field.value)?.label ?? ""
              }
              selectedOptions={field.value ? [field.value] : []}
              onOptionSelect={(_, data) => {
                field.onChange(data.optionValue);
              }}
              placeholder="Wybierz kategorię"
              disabled={isLoading}
            >
              {categories.map((category) => (
                <Option key={category.code} value={category.code}>
                  {category.label}
                </Option>
              ))}
            </Dropdown>
          </Field>
        )}
      />

      <Controller
        name="isManualMode"
        control={control}
        render={({ field }) => (
          <Field label="Tryb wprowadzania">
            <Switch
              checked={field.value}
              onChange={(_, data) => {
                field.onChange(data.checked);
                // Clear fields when switching modes
                if (data.checked) {
                  setValue("description", "");
                } else {
                  setValue("manualCalories", null);
                }
              }}
              label="Wprowadź kalorie ręcznie"
              disabled={isLoading}
            />
          </Field>
        )}
      />

      {!isManualMode ? (
        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <Field
              label="Opis posiłku"
              required
              validationMessage={errors.description?.message}
              validationState={errors.description ? "error" : "none"}
              hint="Opisz co zjadłeś, np. '2 jajka na twardo, kromka chleba z masłem, szklanka mleka'"
            >
              <Textarea
                {...field}
                rows={4}
                placeholder="Wprowadź opis swojego posiłku..."
                maxLength={2000}
                disabled={isLoading}
              />
            </Field>
          )}
        />
      ) : (
        <Controller
          name="manualCalories"
          control={control}
          render={({ field }) => (
            <Field
              label="Kalorie"
              required
              validationMessage={errors.manualCalories?.message}
              validationState={errors.manualCalories ? "error" : "none"}
              hint="Podaj liczbę kalorii w kcal"
            >
              <Input
                type="number"
                value={field.value?.toString() ?? ""}
                onChange={(_, data) => {
                  const value = data.value ? parseFloat(data.value) : null;
                  field.onChange(value);
                }}
                placeholder="np. 450"
                min={1}
                disabled={isLoading}
              />
            </Field>
          )}
        />
      )}

      <div className={styles.buttonGroup}>
        <Button
          appearance="primary"
          type="submit"
          disabled={isLoading}
        >
          {isManualMode ? "Zapisz" : "Analizuj"}
        </Button>
      </div>
    </form>
  );
}

