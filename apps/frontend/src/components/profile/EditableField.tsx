import { useState, useEffect } from "react";
import {
  Button,
  Input,
  Label,
  Text,
  makeStyles,
  shorthands,
  tokens,
  Spinner,
} from "@fluentui/react-components";
import { EditRegular, CheckmarkRegular, DismissRegular } from "@fluentui/react-icons";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("8px"),
  },
  viewMode: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.gap("12px"),
  },
  valueText: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
  },
  editMode: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap("12px"),
  },
  inputRow: {
    display: "flex",
    ...shorthands.gap("8px"),
    alignItems: "flex-start",
  },
  input: {
    flexGrow: 1,
  },
  buttonGroup: {
    display: "flex",
    ...shorthands.gap("8px"),
  },
  errorText: {
    color: tokens.colorPaletteRedForeground1,
    fontSize: tokens.fontSizeBase200,
  },
});

type EditableFieldProps = {
  label: string;
  initialValue: number | null | undefined;
  isUpdating: boolean;
  onSave: (newValue: number) => Promise<void>;
};

export function EditableField({
  label,
  initialValue,
  isUpdating,
  onSave,
}: EditableFieldProps): JSX.Element {
  const styles = useStyles();
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(initialValue?.toString() ?? "");
  const [error, setError] = useState<string | null>(null);

  // Update local value when initialValue changes (after successful save)
  useEffect(() => {
    setValue(initialValue?.toString() ?? "");
  }, [initialValue]);

  const validateValue = (val: string): boolean => {
    setError(null);

    if (!val.trim()) {
      setError("Wartość jest wymagana");
      return false;
    }

    const numValue = Number(val);
    if (isNaN(numValue) || !Number.isInteger(numValue)) {
      setError("Wartość musi być liczbą całkowitą");
      return false;
    }

    if (numValue <= 0) {
      setError("Cel musi być liczbą większą od 0");
      return false;
    }

    return true;
  };

  const handleEdit = () => {
    setValue(initialValue?.toString() ?? "");
    setError(null);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setValue(initialValue?.toString() ?? "");
    setError(null);
    setIsEditing(false);
  };

  const handleSave = async () => {
    if (!validateValue(value)) {
      return;
    }

    try {
      await onSave(Number(value));
      setIsEditing(false);
      setError(null);
    } catch {
      // Error is handled by the hook (toast + error state)
      // We stay in edit mode to allow user to retry
    }
  };

  const handleValueChange = (newValue: string) => {
    setValue(newValue);
    // Clear error on change to provide immediate feedback
    if (error) {
      setError(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      void handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  if (!isEditing) {
    return (
      <div className={styles.container}>
        <Label>{label}</Label>
        <div className={styles.viewMode}>
          <Text className={styles.valueText}>{initialValue ?? 0} kcal</Text>
          <Button
            appearance="subtle"
            icon={<EditRegular />}
            onClick={handleEdit}
            aria-label={`Edytuj ${label.toLowerCase()}`}
            data-testid="calorie-goal-edit-button"
          >
            Edytuj
          </Button>
        </div>
      </div>
    );
  }

  const isValid = !error && value.trim() !== "";
  const isSaving = isUpdating;

  return (
    <div className={styles.container}>
      <Label htmlFor={`edit-${label}`}>{label}</Label>
      <div className={styles.editMode}>
        <div className={styles.inputRow}>
          <Input
            id={`edit-${label}`}
            className={styles.input}
            type="number"
            value={value}
            onChange={(e) => handleValueChange(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSaving}
            aria-invalid={!!error}
            aria-describedby={error ? `error-${label}` : undefined}
            autoFocus
            data-testid="calorie-goal-input"
          />
          <div className={styles.buttonGroup}>
            <Button
              appearance="primary"
              icon={isSaving ? <Spinner size="tiny" /> : <CheckmarkRegular />}
              onClick={() => void handleSave()}
              disabled={!isValid || isSaving}
              aria-label="Zapisz"
              data-testid="calorie-goal-save-button"
            >
              {isSaving ? "Zapisywanie..." : "Zapisz"}
            </Button>
            <Button
              appearance="secondary"
              icon={<DismissRegular />}
              onClick={handleCancel}
              disabled={isSaving}
              aria-label="Anuluj"
              data-testid="calorie-goal-cancel-button"
            >
              Anuluj
            </Button>
          </div>
        </div>
        {error && (
          <Text id={`error-${label}`} className={styles.errorText} role="alert" data-testid="calorie-goal-error">
            {error}
          </Text>
        )}
      </div>
    </div>
  );
}

