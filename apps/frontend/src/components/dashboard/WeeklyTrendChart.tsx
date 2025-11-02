import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Card,
  CardHeader,
  Text,
  makeStyles,
  tokens,
  shorthands,
} from "@fluentui/react-components";
import type { WeeklyTrendReportPointDTO } from "@/types";
import { useTheme } from "@/lib/ThemeProvider";

type WeeklyTrendChartProps = {
  data: WeeklyTrendReportPointDTO[];
};

const useStyles = makeStyles({
  card: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    ...shorthands.gap("16px"),
  },
  header: {
    paddingBottom: "0px",
  },
  chartContainer: {
    height: "300px",
    width: "100%",
  },
  visuallyHidden: {
    clip: "rect(0 0 0 0)",
    clipPath: "inset(50%)",
    height: "1px",
    overflow: "hidden",
    position: "absolute",
    whiteSpace: "nowrap",
    width: "1px",
  },
});

type TooltipProps = {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
};

const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
  const { theme } = useTheme();
  if (active && payload?.length) {
    return (
      <div
        style={{
          backgroundColor:
            theme === "light"
              ? "rgba(255, 255, 255, 0.9)"
              : "rgba(0, 0, 0, 0.9)",
          border: `1px solid ${tokens.colorNeutralStroke2}`,
          borderRadius: tokens.borderRadiusMedium,
          padding: tokens.spacingHorizontalS,
          boxShadow: tokens.shadow4,
        }}
      >
        <p style={{ margin: 0, color: tokens.colorNeutralForeground1 }}>{label}</p>
        <p style={{ margin: 0, color: tokens.colorBrandForeground1 }}>
          {`Calories: ${payload[0].value}`}
        </p>
      </div>
    );
  }

  return null;
};

export const WeeklyTrendChart = ({ data }: WeeklyTrendChartProps) => {
  const styles = useStyles();
  const { theme } = useTheme();

  const chartData = data.map((point) => ({
    date: new Date(point.date).toLocaleDateString("pl-PL", {
      month: "short",
      day: "numeric",
    }),
    calories: point.calories,
    goal: point.goal,
  }));

  const goalValue = data.find((p) => p.goal > 0)?.goal ?? 0;

  const calories = data.map((p) => p.calories);
  const minCalories = Math.min(...calories);
  const maxCalories = Math.max(...calories);
  const avgCalories = Math.round(
    calories.reduce((a, b) => a + b, 0) / calories.length,
  );
  const summaryText = `Trend tygodniowy kalorii: minimum ${minCalories}, maksimum ${maxCalories}, średnia ${avgCalories} kalorii`;

  return (
    <Card data-testid="dashboard-weekly-chart" className={styles.card}>
      <CardHeader
        className={styles.header}
        header={<Text size={500} weight="semibold">Trend tygodniowy</Text>}
        description={
          <Text size={300} style={{ color: tokens.colorNeutralForeground2 }}>Spożycie kalorii w ostatnich 7 dniach</Text>
        }
      />
      <div>
        <span className={styles.visuallyHidden}>{summaryText}</span>
        <div className={styles.chartContainer}>
          <ResponsiveContainer>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke={tokens.colorNeutralStroke2}
              />
              <XAxis
                dataKey="date"
                tickLine={false}
                tickMargin={10}
                axisLine={false}
                stroke={tokens.colorNeutralForeground2}
                tick={{ fill: tokens.colorNeutralForeground2 }}
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                tickMargin={10}
                stroke={tokens.colorNeutralForeground2}
                tick={{ fill: tokens.colorNeutralForeground2 }}
                tickFormatter={(value) =>
                  Number(value).toLocaleString("pl-PL", {
                    maximumFractionDigits: 0,
                  })
                }
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{
                  fill:
                    theme === "light"
                      ? "rgba(0, 0, 0, 0.1)"
                      : "rgba(255, 255, 255, 0.1)",
                }}
              />
              {goalValue > 0 && (
                <ReferenceLine
                  y={goalValue}
                  stroke={tokens.colorNeutralForeground2}
                  strokeDasharray="3 3"
                  strokeWidth={2}
                  label={{
                    value: "Cel",
                    position: "right",
                    fill: tokens.colorNeutralForeground2,
                  }}
                />
              )}
              <Bar
                dataKey="calories"
                fill={tokens.colorBrandBackground}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
};

