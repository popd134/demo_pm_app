import { useRef, useState, type MouseEvent } from "react";
import {
  type LineSeries,
  type SeriesPoint,
  extent,
  formatDate,
  makeScale,
  niceTicks,
} from "./geometry";
import "./charts.css";

export interface Band {
  name: string;
  upper: SeriesPoint[];
  lower: SeriesPoint[];
}

interface LineChartProps {
  series: LineSeries[];
  band?: Band;
  unit?: string;
  height?: number;
  ariaLabel?: string;
}

const WIDTH = 640;
const PAD = { top: 12, right: 16, bottom: 26, left: 40 };

/**
 * Dependency-free time-series line chart with an optional min/max band, a crosshair
 * tooltip, and multi-series overlays (WBS 1.4.4). Uses one y-axis by design.
 */
export function LineChart({ series, band, unit, height = 240, ariaLabel }: LineChartProps) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [hoverX, setHoverX] = useState<number | null>(null);

  const allPoints = series.flatMap((s) => s.points);
  const xs = allPoints.map((p) => p.x);
  const ys = [
    ...allPoints.map((p) => p.y),
    ...(band ? [...band.upper, ...band.lower].map((p) => p.y) : []),
  ].filter((y): y is number => y !== null);

  if (xs.length === 0 || ys.length === 0) {
    return <p className="section-subtle">No data in range.</p>;
  }

  const [xMin, xMax] = extent(xs);
  const [yMinRaw, yMaxRaw] = extent(ys);
  const ticks = niceTicks(yMinRaw, yMaxRaw, 4);
  const yMin = Math.min(yMinRaw, ticks[0] ?? yMinRaw);
  const yMax = Math.max(yMaxRaw, ticks[ticks.length - 1] ?? yMaxRaw);

  const xScale = makeScale({
    domainMin: xMin,
    domainMax: xMax,
    rangeMin: PAD.left,
    rangeMax: WIDTH - PAD.right,
  });
  const yScale = makeScale({
    domainMin: yMin,
    domainMax: yMax,
    rangeMin: height - PAD.bottom,
    rangeMax: PAD.top,
  });

  const linePath = (points: SeriesPoint[]): string =>
    points
      .filter((p): p is { x: number; y: number } => p.y !== null)
      .map((p, i) => `${i === 0 ? "M" : "L"}${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`)
      .join(" ");

  const bandPath = (): string => {
    if (!band) return "";
    const up = band.upper.filter((p): p is { x: number; y: number } => p.y !== null);
    const lo = band.lower.filter((p): p is { x: number; y: number } => p.y !== null);
    if (up.length === 0 || lo.length === 0) return "";
    const upSeg = up.map((p) => `${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`).join(" L");
    const loSeg = [...lo]
      .reverse()
      .map((p) => `${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`)
      .join(" L");
    return `M${upSeg} L${loSeg} Z`;
  };

  // Nearest sample to the hovered x-position (across the first series' timestamps).
  const primary = series[0].points.filter((p): p is { x: number; y: number } => p.y !== null);
  const hoverPoint =
    hoverX !== null && primary.length > 0
      ? primary.reduce((best, p) =>
          Math.abs(p.x - hoverX) < Math.abs(best.x - hoverX) ? p : best,
        )
      : null;

  function handleMove(evt: MouseEvent<SVGSVGElement>) {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const px = ((evt.clientX - rect.left) / rect.width) * WIDTH;
    const ratio = (px - PAD.left) / (WIDTH - PAD.right - PAD.left);
    setHoverX(xMin + Math.min(1, Math.max(0, ratio)) * (xMax - xMin));
  }

  return (
    <div className="chart">
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label={ariaLabel ?? "Line chart"}
        className="chart__svg"
        onMouseMove={handleMove}
        onMouseLeave={() => setHoverX(null)}
      >
        {ticks.map((t) => (
          <g key={t}>
            <line
              className="chart__grid"
              x1={PAD.left}
              x2={WIDTH - PAD.right}
              y1={yScale(t)}
              y2={yScale(t)}
            />
            <text className="chart__axis-label" x={PAD.left - 6} y={yScale(t) + 3} textAnchor="end">
              {t}
            </text>
          </g>
        ))}

        {[xMin, (xMin + xMax) / 2, xMax].map((x) => (
          <text
            key={x}
            className="chart__axis-label"
            x={xScale(x)}
            y={height - PAD.bottom + 16}
            textAnchor="middle"
          >
            {formatDate(x)}
          </text>
        ))}

        {band && <path className="chart__band" d={bandPath()} />}

        {series.map((s) => (
          <path
            key={s.name}
            d={linePath(s.points)}
            fill="none"
            style={{ stroke: s.color }}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}

        {hoverPoint && (
          <g>
            <line
              className="chart__crosshair"
              x1={xScale(hoverPoint.x)}
              x2={xScale(hoverPoint.x)}
              y1={PAD.top}
              y2={height - PAD.bottom}
            />
            <circle
              cx={xScale(hoverPoint.x)}
              cy={yScale(hoverPoint.y)}
              r={4}
              style={{ fill: series[0].color }}
            />
          </g>
        )}
      </svg>

      {hoverPoint && (
        <div className="chart__tooltip">
          <strong>{formatDate(hoverPoint.x)}</strong>: {hoverPoint.y.toFixed(1)}
          {unit ? ` ${unit}` : ""}
        </div>
      )}

      {(series.length > 1 || band) && (
        <div className="chart__legend">
          {series.map((s) => (
            <span key={s.name} className="chart__legend-item">
              <span className="chart__swatch" style={{ background: s.color }} />
              {s.name}
            </span>
          ))}
          {band && (
            <span className="chart__legend-item">
              <span className="chart__swatch chart__swatch--band" />
              {band.name}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
