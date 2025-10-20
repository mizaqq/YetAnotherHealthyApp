import React from "react";
import { ThemeToggle } from "@/components/common/ThemeToggle";
import { makeStyles, shorthands, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  root: {
    position: "relative",
    minHeight: "100vh",
    width: "100%",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  themeToggle: {
    position: "fixed",
    top: tokens.spacingVerticalL,
    right: tokens.spacingHorizontalL,
    zIndex: 50,
  },
  content: {
    display: "flex",
    minHeight: "100vh",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding("24px"),
  },
});

export function AuthPageLayout({
  children,
}: {
  children: React.ReactNode;
}): JSX.Element {
  const styles = useStyles();
  return (
    <div className={styles.root}>
      <div className={styles.themeToggle}>
        <ThemeToggle />
      </div>
      <div className={styles.content}>{children}</div>
    </div>
  );
}
