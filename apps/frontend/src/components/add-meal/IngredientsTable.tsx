import {
  Table,
  TableBody,
  TableCell,
  TableCellLayout,
  TableHeader,
  TableHeaderCell,
  TableRow,
  makeStyles,
  tokens,
  Text,
} from "@fluentui/react-components";
import type { AnalysisRunItemDTO, MealAnalysisItemDTO } from "@/types";

type IngredientsTableProps = {
  items: AnalysisRunItemDTO[] | MealAnalysisItemDTO[];
};

const useStyles = makeStyles({
  table: {
    width: "100%",
  },
  headerCell: {
    fontWeight: tokens.fontWeightSemibold,
  },
  numberCell: {
    textAlign: "right",
  },
  confidenceCell: {
    textAlign: "right",
  },
  confidenceHigh: {
    color: tokens.colorPaletteGreenForeground1,
  },
  confidenceMedium: {
    color: tokens.colorPaletteYellowForeground2,
  },
  confidenceLow: {
    color: tokens.colorPaletteRedForeground1,
  },
});

export function IngredientsTable({ items }: IngredientsTableProps) {
  const styles = useStyles();

  const getConfidenceStyle = (confidence: number) => {
    if (confidence >= 0.8) return styles.confidenceHigh;
    if (confidence >= 0.5) return styles.confidenceMedium;
    return styles.confidenceLow;
  };

  if (items.length === 0) {
    return (
      <Text size={400} style={{ color: tokens.colorNeutralForeground2 }}>
        Brak składników do wyświetlenia
      </Text>
    );
  }

  return (
    <Table className={styles.table} size="small" aria-label="Tabela składników">
      <TableHeader>
        <TableRow>
          <TableHeaderCell className={styles.headerCell}>Lp.</TableHeaderCell>
          <TableHeaderCell className={styles.headerCell}>Składnik</TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.numberCell}`}>
            Waga (g)
          </TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.numberCell}`}>
            Kalorie
          </TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.numberCell}`}>
            Białko (g)
          </TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.numberCell}`}>
            Tłuszcz (g)
          </TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.numberCell}`}>
            Węgl. (g)
          </TableHeaderCell>
          <TableHeaderCell className={`${styles.headerCell} ${styles.confidenceCell}`}>
            Pewność
          </TableHeaderCell>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell>
              <TableCellLayout>{item.ordinal}</TableCellLayout>
            </TableCell>
            <TableCell>
              <TableCellLayout>{item.raw_name}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.numberCell}>
              <TableCellLayout>{(item.weight_grams ?? 0).toFixed(1)}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.numberCell}>
              <TableCellLayout>{(item.calories ?? 0).toFixed(0)}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.numberCell}>
              <TableCellLayout>{(item.protein ?? 0).toFixed(1)}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.numberCell}>
              <TableCellLayout>{(item.fat ?? 0).toFixed(1)}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.numberCell}>
              <TableCellLayout>{(item.carbs ?? 0).toFixed(1)}</TableCellLayout>
            </TableCell>
            <TableCell className={styles.confidenceCell}>
              <TableCellLayout>
                <Text className={getConfidenceStyle(item.confidence ?? 0)}>
                  {((item.confidence ?? 0) * 100).toFixed(0)}%
                </Text>
              </TableCellLayout>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

