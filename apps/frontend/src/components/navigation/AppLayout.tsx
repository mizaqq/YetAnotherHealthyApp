import React, { useState } from "react";
import { makeStyles, tokens } from "@fluentui/react-components";
import { BottomTabBar } from "./BottomTabBar";
import { FloatingActionButton } from "./FloatingActionButton";
import { AddMealDialog } from "@/components/add-meal/AddMealDialog";
import { useDashboardRefresh } from "@/lib/DashboardRefreshContext";

type AppLayoutProps = {
  children: React.ReactNode;
};

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  content: {
    paddingBottom: "calc(72px + env(safe-area-inset-bottom))",
  },
});

export function AppLayout({ children }: AppLayoutProps): JSX.Element {
  const styles = useStyles();
  const [addMealDialogOpen, setAddMealDialogOpen] = useState(false);
  const { refresh } = useDashboardRefresh();

  const handleAddMealSuccess = () => {
    refresh();
  };

  return (
    <div className={styles.root}>
      <main className={styles.content}>{children}</main>
      <FloatingActionButton onClick={() => setAddMealDialogOpen(true)} />
      <BottomTabBar />
      <AddMealDialog
        open={addMealDialogOpen}
        onOpenChange={setAddMealDialogOpen}
        onSuccess={handleAddMealSuccess}
      />
    </div>
  );
}


