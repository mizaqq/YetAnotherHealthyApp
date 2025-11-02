import { useEffect, useRef } from "react";
import { Spinner, Text, makeStyles, shorthands, tokens } from "@fluentui/react-components";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding(tokens.spacingVerticalXXL),
    ...shorthands.gap(tokens.spacingVerticalM),
  },
  error: {
    color: tokens.colorPaletteRedForeground1,
  },
});

type InfiniteScrollLoaderProps = {
  onLoadMore: () => void;
  isLoading: boolean;
  hasMore: boolean;
  error?: Error | null;
};

/**
 * InfiniteScrollLoader detects when user scrolls to bottom of list
 * and triggers loading of more data using Intersection Observer API
 */
export function InfiniteScrollLoader({
  onLoadMore,
  isLoading,
  hasMore,
  error,
}: InfiniteScrollLoaderProps) {
  const styles = useStyles();
  const observerTarget = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasMore || isLoading || error) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          onLoadMore();
        }
      },
      {
        threshold: 0.1,
        rootMargin: "100px",
      }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [onLoadMore, isLoading, hasMore, error]);

  if (!hasMore && !isLoading && !error) {
    return null;
  }

  return (
    <div ref={observerTarget} className={styles.container}>
      {isLoading && (
        <>
          <Spinner size="medium" />
          <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>
            Ładowanie...
          </Text>
        </>
      )}
      {error && (
        <div className={styles.error}>
          <Text size={300}>Nie udało się załadować więcej posiłków.</Text>
          <button
            onClick={onLoadMore}
            style={{
              cursor: "pointer",
              textDecoration: "underline",
              background: "none",
              border: "none",
              padding: 0,
              color: tokens.colorBrandForeground1,
              fontSize: tokens.fontSizeBase300,
            }}
          >
            Spróbuj ponownie
          </button>
        </div>
      )}
    </div>
  );
}

