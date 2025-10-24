import { Text, makeStyles, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  header: {
    paddingTop: tokens.spacingVerticalL,
    paddingBottom: tokens.spacingVerticalM,
  },
});

type DateGroupHeaderProps = {
  date: string;
};

/**
 * DateGroupHeader displays a date header for grouped meals
 * Shows formatted date like "Dzisiaj", "Wczoraj", or "16 października 2025"
 */
export function DateGroupHeader({ date }: DateGroupHeaderProps) {
  const styles = useStyles();

  const formatDateHeader = (dateStr: string): string => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    // Reset time parts for comparison
    today.setHours(0, 0, 0, 0);
    yesterday.setHours(0, 0, 0, 0);
    date.setHours(0, 0, 0, 0);

    if (date.getTime() === today.getTime()) {
      return "Dzisiaj";
    }
    if (date.getTime() === yesterday.getTime()) {
      return "Wczoraj";
    }

    return date.toLocaleDateString("pl-PL", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <li className={styles.header}>
      <Text as="h3" size={500} weight="semibold">
        {formatDateHeader(date)}
      </Text>
    </li>
  );
}

