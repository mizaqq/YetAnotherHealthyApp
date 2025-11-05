import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { Warning24Regular } from "@fluentui/react-icons";

type DeleteMealDialogProps = {
  open: boolean;
  meal: { id: string; category: string; calories: number } | null;
  onOpenChange: (open: boolean) => void;
  onConfirm: (mealId: string) => void;
  isDeleting: boolean;
};

const useStyles = makeStyles({
  surface: {
    maxWidth: "480px",
  },
  warningIcon: {
    color: tokens.colorPaletteRedForeground1,
  },
  warningSection: {
    display: "flex",
    alignItems: "flex-start",
    ...shorthands.gap(tokens.spacingHorizontalM),
    ...shorthands.padding(tokens.spacingVerticalM, 0),
  },
  warningContent: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  mealInfo: {
    ...shorthands.padding(tokens.spacingVerticalM),
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
  },
  deleteButton: {
    backgroundColor: tokens.colorPaletteRedBackground3,
    color: tokens.colorNeutralForegroundOnBrand,
    ":hover": {
      backgroundColor: tokens.colorPaletteRedBackground2,
    },
  },
});

export function DeleteMealDialog({
  open,
  meal,
  onOpenChange,
  onConfirm,
  isDeleting,
}: DeleteMealDialogProps) {
  const styles = useStyles();

  if (!meal) {
    return null;
  }

  const handleConfirm = () => {
    onConfirm(meal.id);
  };

  return (
    <Dialog open={open} onOpenChange={(_, data) => onOpenChange(data.open)}>
      <DialogSurface className={styles.surface}>
        <DialogBody>
          <DialogTitle>Usuń posiłek</DialogTitle>
          <DialogContent>
            <div className={styles.warningSection}>
              <Warning24Regular className={styles.warningIcon} />
              <div className={styles.warningContent}>
                <Text weight="semibold">Czy na pewno chcesz usunąć ten posiłek?</Text>
                <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                  Operacji nie można cofnąć.
                </Text>
              </div>
            </div>
            <div className={styles.mealInfo}>
              <Text weight="semibold">{meal.category}</Text>
              <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                {meal.calories.toFixed(0)} kcal
              </Text>
            </div>
          </DialogContent>
          <DialogActions>
            <Button appearance="secondary" onClick={() => onOpenChange(false)} disabled={isDeleting}>
              Anuluj
            </Button>
            <Button
              appearance="primary"
              onClick={handleConfirm}
              disabled={isDeleting}
              className={styles.deleteButton}
            >
              {isDeleting ? "Usuwanie..." : "Usuń"}
            </Button>
          </DialogActions>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

