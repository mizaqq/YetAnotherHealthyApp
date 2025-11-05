import {
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import { FoodPizza24Regular } from "@fluentui/react-icons";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    ...shorthands.padding("48px", "24px"),
    ...shorthands.border(
      "2px",
      "dashed",
      tokens.colorNeutralStroke2,
    ),
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    backgroundColor: tokens.colorNeutralBackground2,
  },
  iconContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "64px",
    height: "64px",
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
    backgroundColor: tokens.colorBrandBackground2,
    marginBottom: tokens.spacingVerticalL,
  },
  icon: {
    color: tokens.colorBrandForeground2,
    fontSize: "32px",
  },
  title: {
    marginBottom: tokens.spacingVerticalS,
  },
  description: {
    color: tokens.colorNeutralForeground2,
    maxWidth: "400px",
  },
});

/**
 * Empty state for when no meals have been added for the day
 * Note: Use the global FAB button to add meals
 */
export function EmptyState(): JSX.Element {
  const styles = useStyles();

  return (
    <div className={styles.root}>
      <div className={styles.iconContainer}>
        <FoodPizza24Regular className={styles.icon} />
      </div>
      <Text as="h2" size={600} weight="semibold" className={styles.title}>
        Nie dodałeś jeszcze posiłku
      </Text>
      <Text as="p" size={400} className={styles.description}>
        Zacznij śledzić swoje odżywianie dodając pierwszy posiłek dzisiaj.
        Użyj przycisku + na dole ekranu.
      </Text>
    </div>
  );
}

