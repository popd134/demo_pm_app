import { useState } from "react";
import { type SeriesPoint, extent, formatDate, makeScale, niceTicks } from "./geometry";
import "./charts.css";

interface BarChartProps {
  points: SeriesPoint[];
  color: string;
  unit?: string;
  height?: number;
  ariaLabel?: string;
}

const WIDTH = 640;
const PAD = { top: 12, right: 16, bottom: 26, left: 40 };

/** Dependency-free bar chart anchored to the baseline, with per-bar hover (WBS 1.4.4). */
export function BarChart({ points, color, unit, height = 220, ariaLabel }: BarChartProps) {
  const [hover, setHover] = useState<number | null>(null);

  const valued = points.filter((p): p is { x: number; y: number } => p.y !== null);
  if (valued.length === 0) {
    return <p className="section-subtle">No data in range.</p>;
  }

  const xs = valued.map((p) => p.x);
  const ys = valued.map((p) => p.y);
  const [xMin, xMax] = extent(xs);
  const yMax = Math.max(0, ...ys);
  const ticks = niceTicks(0, yMax, 4);
  const top = Math.max(yMax, ticks[ticks.length - 1] ?? yMax);

  const xScale = makeScale({
    domainMin: xMin,
    domainMax: xMax,
    rangeMin: PAD.left,
    rangeMax: WIDTH - PAD.right,
  });
  const yScale = makeScale({
    domainMin: 0,
    domainMax: top,
    rangeMin: height - PAD.bottom,
    rangeMax: PAD.top,
  });

  const slot = (WIDTH - PAD.right - PAD.left) / valued.length;
  const barWidth = Math.max(2, Math.min(28, slot - 6));
  const baseline = yScale(0);

  return (
    <div className="chart">
      <svg viewBox={`0 0 ${WIDTH} ${height}`} role="img" aria-label={ariaLabel ?? "Bar chart"} className="chart__svg">
        {ticks.map((t) => (
          <g key={t}>
            <line className="chart__grid" x1={PAD.left} x2={WIDTH - PAD.right} y1={yScale(t)} y2={yScale(t)} />
            <text className="chart__axis-label" x={PAD.left - 6} y={yScale(t) + 3} textAnchor="end">
              {t}
            </text>
          </g>
        ))}

        {valued.map((p, i) => {
          const h = baseline - yScale(p.y);
          const cx = xScale(p.x);
          return (
            <rect
              key={p.x}
              x={cx - barWidth / 2}
              y={yScale(p.y)}
              width={barWidth}
              height={Math.max(0, h)}
              rx={4}
              style={{ fill: color }}
              opacity={hover === null || hover === i ? 1 : 0.55}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
            />
          );
        })}

        {[xMin, xMax].map((x) => (
          <text key={x} className="chart__axis-label" x={xScale(x)} y={height - PAD.bottom + 16} textAnchor="middle">
            {formatDate(x)}
          </text>
        ))}
      </svg>

      {hover !== null && (
        <div className="chart__tooltip">
          <strong>{formatDate(valued[hover].x)}</strong>: {valued[hover].y.toFixed(1)}
          {unit ? ` ${unit}` : ""}
        </div>
      )}
    </div>
  );
}
