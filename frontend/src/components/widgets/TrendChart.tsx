import { useState } from "react";
import { EmptyState, ErrorState, Skeleton } from "../ui";
import { BarChart } from "../charts/BarChart";
import { LineChart } from "../charts/LineChart";
import type { SeriesPoint } from "../charts/geometry";
import { useQuery } from "../../hooks/useQuery";
import { getTrends, type AggregateBucket, type AggregatePeriod } from "../../lib/api";

const PERIODS: AggregatePeriod[] = ["daily", "weekly", "monthly"];
const SERIES_1 = "var(--viz-series-1)";

interface TrendChartProps {
  locationId: number;
  metric: string;
  unit: string;
  kind: "line" | "bar";
}

/**
 * Interactive trend chart with a period range selector (WBS 1.4.4), backed by the
 * cached query layer (WBS 1.5.2) so revisiting a period is instant.
 */
export function TrendChart({ locationId, metric, unit, kind }: TrendChartProps) {
  const [period, setPeriod] = useState<AggregatePeriod>("daily");

  const { data, isLoading, isError, refetch } = useQuery(
    `trends:${locationId}:${metric}:${period}`,
    () => getTrends(locationId, metric, period),
    { staleTime: 60_000 },
  );
  const buckets: AggregateBucket[] | undefined = data?.buckets;
  const isEmpty = !isLoading && !isError && buckets !== undefined && buckets.length === 0;

  const toEpoch = (b: AggregateBucket): number => Date.parse(b.period_start);

  return (
    <div>
      <div className="chart-toolbar" role="group" aria-label="Select range">
        {PERIODS.map((p) => (
          <button
            key={p}
            type="button"
            className={
              "chart-toolbar__button" +
              (p === period ? " chart-toolbar__button--active" : "")
            }
            onClick={() => setPeriod(p)}
          >
            {p}
          </button>
        ))}
      </div>

      {isLoading && <Skeleton height="220px" radius="var(--radius-md)" />}
      {isError && <ErrorState message="Could not load analytics." onRetry={refetch} />}
      {isEmpty && (
        <EmptyState icon="📉" title="No data in range" message="Try a different range or run ingestion." />
      )}
      {!isLoading && !isError && !isEmpty && buckets && kind === "line" && (
        <LineChart
          unit={unit}
          ariaLabel={`${metric} ${period} trend`}
          series={[
            {
              name: "Average",
              color: SERIES_1,
              points: buckets.map((b): SeriesPoint => ({ x: toEpoch(b), y: b.average })),
            },
          ]}
          band={{
            name: "Min–Max",
            upper: buckets.map((b): SeriesPoint => ({ x: toEpoch(b), y: b.maximum })),
            lower: buckets.map((b): SeriesPoint => ({ x: toEpoch(b), y: b.minimum })),
          }}
        />
      )}
      {!isLoading && !isError && !isEmpty && buckets && kind === "bar" && (
        <BarChart
          unit={unit}
          color={SERIES_1}
          ariaLabel={`${metric} ${period} totals`}
          points={buckets.map((b): SeriesPoint => ({ x: toEpoch(b), y: b.total }))}
        />
      )}
    </div>
  );
}
