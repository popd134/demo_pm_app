/** Small charting geometry helpers (WBS 1.4.4). Dependency-free. */

export interface SeriesPoint {
  x: number; // epoch milliseconds
  y: number | null;
}

export interface LineSeries {
  name: string;
  color: string;
  points: SeriesPoint[];
}

export interface Scale {
  domainMin: number;
  domainMax: number;
  rangeMin: number;
  rangeMax: number;
}

export function makeScale(scale: Scale): (value: number) => number {
  const { domainMin, domainMax, rangeMin, rangeMax } = scale;
  const span = domainMax - domainMin || 1;
  return (value: number) =>
    rangeMin + ((value - domainMin) / span) * (rangeMax - rangeMin);
}

export function extent(values: number[]): [number, number] {
  if (values.length === 0) return [0, 1];
  let lo = values[0];
  let hi = values[0];
  for (const v of values) {
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  if (lo === hi) {
    return [lo - 1, hi + 1];
  }
  return [lo, hi];
}

/** Round a numeric domain to "nice" tick values. */
export function niceTicks(min: number, max: number, count = 4): number[] {
  const span = max - min || 1;
  const step = niceStep(span / count);
  const start = Math.ceil(min / step) * step;
  const ticks: number[] = [];
  for (let v = start; v <= max + step * 0.001; v += step) {
    ticks.push(Number(v.toFixed(6)));
  }
  return ticks;
}

function niceStep(rough: number): number {
  const pow = Math.pow(10, Math.floor(Math.log10(rough)));
  const norm = rough / pow;
  const nice = norm >= 5 ? 5 : norm >= 2 ? 2 : 1;
  return nice * pow;
}

export function formatDate(epochMs: number): string {
  return new Date(epochMs).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}
