import {
  Card,
  CardHeader,
  makeStyles,
  shorthands,
  tokens,
  Skeleton,
  SkeletonItem,
} from "@fluentui/react-components";

const useStyles = makeStyles({
  card: {
    display: "flex",
    flexDirection: "column",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingVerticalS),
  },
  content: {
    display: "flex",
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  skeletonCircle: {
    height: "250px",
    width: "250px",
    ...shorthands.borderRadius(tokens.borderRadiusCircular),
  },
});

/**
 * Loading skeleton for chart components
 * Provides visual feedback while charts are loading
 */
export function ChartSkeleton(): JSX.Element {
  const styles = useStyles();
  return (
    <Card className={styles.card}>
      <CardHeader>
        <div className={styles.header}>
          <Skeleton>
            <SkeletonItem style={{ width: "128px" }} />
            <SkeletonItem style={{ width: "96px" }} />
          </Skeleton>
        </div>
      </CardHeader>
      <div className={styles.content}>
        <Skeleton>
          <SkeletonItem className={styles.skeletonCircle} />
        </Skeleton>
      </div>
    </Card>
  );
}

