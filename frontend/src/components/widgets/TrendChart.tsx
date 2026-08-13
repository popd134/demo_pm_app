import { useEffect, useState } from "react";
import { Spinner } from "../ui";
import { BarChart } from "../charts/BarChart";
import { LineChart } from "../charts/LineChart";
import type { SeriesPoint } from "../charts/geometry";
import {
  getTrends,
  type AggregateBucket,
  type AggregatePeriod,
} from "../../lib/api";

const PERIODS: AggregatePeriod[] = ["daily", "weekly", "monthly"];
const SERIES_1 = "var(--viz-series-1)";

interface TrendChartProps {
  locationId: number;
  metric: string;
  unit: string;
  kind: "line" | "bar";
}

/**
 * Fetches aggregated trends for one metric and renders an interactive chart with a
 * period range selector (WBS 1.4.4). Temperature-style metrics show an average line
 * with a min/max band; totals (e.g. precipitation) show bars.
 */
export function TrendChart({ locationId, metric, unit, kind }: TrendChartProps) {
  const [period, setPeriod] = useState<AggregatePeriod>("daily");
  const [buckets, setBuckets] = useState<AggregateBucket[] | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    getTrends(locationId, metric, period)
      .then((res) => {
        if (cancelled) return;
        setBuckets(res.buckets);
        setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [locationId, metric, period]);

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

      {status === "loading" && <Spinner label="Loading chart…" />}
      {status === "error" && <p className="section-subtle">Could not load analytics.</p>}
      {status === "ready" && buckets && kind === "line" && (
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
      {status === "ready" && buckets && kind === "bar" && (
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
