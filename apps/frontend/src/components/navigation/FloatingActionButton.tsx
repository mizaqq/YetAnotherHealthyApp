import { Button, makeStyles, tokens } from "@fluentui/react-components";
import { Add24Filled } from "@fluentui/react-icons";

type FloatingActionButtonProps = {
  onClick: () => void;
  ariaLabel?: string;
};

const useStyles = makeStyles({
  fab: {
    position: "fixed",
    bottom: "calc(56px + 16px + env(safe-area-inset-bottom))",
    right: "16px",
    zIndex: 50,
    width: "64px",
    height: "64px",
    minWidth: "64px",
    minHeight: "64px",
    borderRadius: "50%",
    boxShadow: tokens.shadow28,
    "&:hover": {
      boxShadow: tokens.shadow64,
    },
    "@media (max-width: 640px)": {
      width: "56px",
      height: "56px",
      minWidth: "56px",
      minHeight: "56px",
    },
  },
});

export function FloatingActionButton({
  onClick,
  ariaLabel = "Dodaj posiłek",
}: FloatingActionButtonProps): JSX.Element {
  const styles = useStyles();

  return (
    <Button
      appearance="primary"
      shape="circular"
      icon={<Add24Filled />}
      className={styles.fab}
      onClick={onClick}
      aria-label={ariaLabel}
      size="large"
    />
  );
}


