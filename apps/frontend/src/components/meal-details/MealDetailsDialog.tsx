import { useState } from "react";
import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  Button,
  Text,
  Spinner,
  MessageBar,
  MessageBarBody,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { Dismiss24Regular, Delete24Regular } from "@fluentui/react-icons";
import { toast } from "sonner";
import { useMealDetails } from "@/hooks/useMealDetails";
import { useMealCategories } from "@/hooks/useMealCategories";
import { deleteMeal } from "@/lib/api";
import { MacroDisplay } from "@/components/dashboard/MacroDisplay";
import { IngredientsTable } from "@/components/add-meal/IngredientsTable";
import { DeleteMealDialog } from "./DeleteMealDialog";

type MealDetailsDialogProps = {
  open: boolean;
  mealId: string | null;
  onOpenChange: (open: boolean) => void;
  onDeleted: () => void;
};

const useStyles = makeStyles({
  surface: {
    maxWidth: "800px",
    width: "90vw",
  },
  body: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    ...shorthands.gap(tokens.spacingHorizontalM),
  },
  headerInfo: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
  },
  headerActions: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
  content: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXL),
  },
  section: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  sectionTitle: {
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground2,
  },
  loadingContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding(tokens.spacingVerticalXXXL),
    ...shorthands.gap(tokens.spacingVerticalL),
  },
  emptyState: {
    textAlign: "center",
    ...shorthands.padding(tokens.spacingVerticalXL),
    color: tokens.colorNeutralForeground2,
  },
});

export function MealDetailsDialog({
  open,
  mealId,
  onOpenChange,
  onDeleted,
}: MealDetailsDialogProps) {
  const styles = useStyles();
  const { mealDetails, isLoading, error } = useMealDetails(mealId);
  const { getCategoryLabel } = useMealCategories();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleClose = () => {
    onOpenChange(false);
    setDeleteDialogOpen(false);
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = (mealIdToDelete: string) => {
    void (async () => {
      setIsDeleting(true);
      try {
        await deleteMeal(mealIdToDelete);
        toast.success("Posiłek został usunięty");
        setDeleteDialogOpen(false);
        handleClose();
        onDeleted();
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Nie udało się usunąć posiłku";
        toast.error(errorMessage);
      } finally {
        setIsDeleting(false);
      }
    })();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pl-PL", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <>
      <Dialog open={open} onOpenChange={(_, data) => onOpenChange(data.open)}>
        <DialogSurface className={styles.surface}>
          <DialogBody className={styles.body}>
            <div className={styles.header}>
              <div className={styles.headerInfo}>
                <DialogTitle>
                  {mealDetails ? getCategoryLabel(mealDetails.category) : "Szczegóły posiłku"}
                </DialogTitle>
                {mealDetails && (
                  <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
                    {formatDate(mealDetails.eaten_at)}
                  </Text>
                )}
              </div>
              <div className={styles.headerActions}>
                {mealDetails && (
                  <Button
                    appearance="subtle"
                    icon={<Delete24Regular />}
                    onClick={handleDeleteClick}
                    disabled={isDeleting}
                  >
                    Usuń
                  </Button>
                )}
                <Button
                  appearance="subtle"
                  icon={<Dismiss24Regular />}
                  onClick={handleClose}
                  aria-label="Zamknij"
                />
              </div>
            </div>

            <DialogContent className={styles.content}>
              {isLoading && (
                <div className={styles.loadingContainer}>
                  <Spinner size="large" label="Ładowanie szczegółów..." />
                </div>
              )}

              {error && (
                <MessageBar intent="error">
                  <MessageBarBody>{error}</MessageBarBody>
                </MessageBar>
              )}

              {mealDetails && !isLoading && (
                <>
                  {/* Macros Section */}
                  <div className={styles.section}>
                    <Text className={styles.sectionTitle}>Wartości odżywcze</Text>
                    <MacroDisplay
                      macros={{
                        protein: mealDetails.protein ?? 0,
                        fat: mealDetails.fat ?? 0,
                        carbs: mealDetails.carbs ?? 0,
                      }}
                      calories={mealDetails.calories}
                    />
                  </div>

                  {/* Ingredients Section */}
                  {mealDetails.analysis?.items && mealDetails.analysis.items.length > 0 && (
                    <div className={styles.section}>
                      <Text className={styles.sectionTitle}>Składniki</Text>
                      <IngredientsTable items={mealDetails.analysis.items} />
                    </div>
                  )}

                  {/* Manual meal message */}
                  {mealDetails.source === "manual" && (
                    <div className={styles.emptyState}>
                      <Text>Posiłek ręczny - brak szczegółowych składników</Text>
                    </div>
                  )}

                  {/* AI meal without items */}
                  {mealDetails.source === "ai" &&
                    (!mealDetails.analysis?.items || mealDetails.analysis.items.length === 0) && (
                      <div className={styles.emptyState}>
                        <Text>Brak danych o składnikach</Text>
                      </div>
                    )}
                </>
              )}
            </DialogContent>
          </DialogBody>
        </DialogSurface>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      {mealDetails && (
        <DeleteMealDialog
          open={deleteDialogOpen}
          meal={{
            id: mealDetails.id,
            category: getCategoryLabel(mealDetails.category),
            calories: mealDetails.calories,
          }}
          onOpenChange={setDeleteDialogOpen}
          onConfirm={handleDeleteConfirm}
          isDeleting={isDeleting}
        />
      )}
    </>
  );
}

