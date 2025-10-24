import { useEffect } from "react";
import {
  Dialog,
  DialogSurface,
  DialogBody,
  DialogTitle,
  DialogContent,
  Button,
  makeStyles,
  tokens,
  shorthands,
  MessageBar,
  MessageBarBody,
} from "@fluentui/react-components";
import { Dismiss24Regular } from "@fluentui/react-icons";
import { useAddMealStepper } from "@/hooks/useAddMealStepper";
import { MealInputStep } from "./MealInputStep";
import { AnalysisLoadingStep } from "./AnalysisLoadingStep";
import { AnalysisResultsStep } from "./AnalysisResultsStep";

type AddMealDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
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
  content: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  errorBar: {
    marginBottom: tokens.spacingVerticalM,
  },
});

export function AddMealDialog({
  open,
  onOpenChange,
  onSuccess,
}: AddMealDialogProps) {
  const styles = useStyles();

  const {
    step,
    formData,
    analysisResults,
    error,
    isSubmitting,
    categories,
    isCategoriesLoading,
    loadCategories,
    handleStartAnalysis,
    handleAcceptResults,
    handleRetryAnalysis,
    handleCreateManualMeal,
    handleCancel,
    handleReset,
  } = useAddMealStepper();

  // Load categories on mount (eagerly, before dialog opens)
  useEffect(() => {
    void loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  const handleClose = () => {
    handleReset();
    onOpenChange(false);
  };

  const handleInputSubmit = (data: typeof formData) => {
    void (async () => {
      if (data.isManualMode) {
        const success = await handleCreateManualMeal(data);
        if (success) {
          onSuccess();
          handleClose();
        }
      } else {
        await handleStartAnalysis(data);
      }
    })();
  };

  const handleAccept = () => {
    void (async () => {
      const success = await handleAcceptResults();
      if (success) {
        onSuccess();
        handleClose();
      }
    })();
  };

  const handleCancelWithClose = () => {
    void handleCancel();
    // Don't close dialog, just go back to input step
  };

  const getDialogTitle = () => {
    switch (step) {
      case "input":
        return "Dodaj posiłek";
      case "loading":
        return "Analiza posiłku";
      case "results":
        return "Wyniki analizy";
      default:
        return "Dodaj posiłek";
    }
  };

  return (
    <Dialog open={open} onOpenChange={(_, data) => onOpenChange(data.open)}>
      <DialogSurface className={styles.surface}>
        <DialogBody className={styles.body}>
          <div className={styles.header}>
            <DialogTitle>{getDialogTitle()}</DialogTitle>
            <Button
              appearance="subtle"
              aria-label="Zamknij"
              icon={<Dismiss24Regular />}
              onClick={handleClose}
            />
          </div>
          <DialogContent className={styles.content}>
            {error && step === "input" && (
              <MessageBar intent="error" className={styles.errorBar}>
                <MessageBarBody>{error}</MessageBarBody>
              </MessageBar>
            )}

            {step === "input" && (
              <MealInputStep
                initialData={formData}
                categories={categories}
                isLoading={isSubmitting || isCategoriesLoading}
                onSubmit={handleInputSubmit}
              />
            )}

            {step === "loading" && (
              <AnalysisLoadingStep onCancel={handleCancelWithClose} />
            )}

            {step === "results" && analysisResults && (
              <>
                {error && (
                  <MessageBar intent="error" className={styles.errorBar}>
                    <MessageBarBody>{error}</MessageBarBody>
                  </MessageBar>
                )}
                <AnalysisResultsStep
                  results={analysisResults}
                  isLoading={isSubmitting}
                  onAccept={handleAccept}
                  onRetry={() => void handleRetryAnalysis()}
                  onCancel={handleClose}
                />
              </>
            )}
          </DialogContent>
        </DialogBody>
      </DialogSurface>
    </Dialog>
  );
}

