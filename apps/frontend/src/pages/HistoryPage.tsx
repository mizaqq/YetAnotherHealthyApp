import { Title1, Text, makeStyles, shorthands, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
    backgroundColor: tokens.colorNeutralBackground1,
  },
  container: {
    maxWidth: "1280px",
    ...shorthands.margin("0", "auto"),
    ...shorthands.padding(tokens.spacingVerticalXXL, tokens.spacingHorizontalXXL),
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalL),
  },
});

export default function HistoryPage() {
  const styles = useStyles();

  return (
    <div className={styles.root}>
      <div className={styles.container}>
        <Title1 as="h1">Historia</Title1>
        <Text size={400}>Widok w przygotowaniu...</Text>
      </div>
    </div>
  );
}


