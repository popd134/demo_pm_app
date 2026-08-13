import { describe, expect, it } from "vitest";
import { extent, makeScale, niceTicks } from "./geometry";

describe("geometry", () => {
  it("makeScale maps domain to range linearly", () => {
    const scale = makeScale({ domainMin: 0, domainMax: 10, rangeMin: 0, rangeMax: 100 });
    expect(scale(0)).toBe(0);
    expect(scale(5)).toBe(50);
    expect(scale(10)).toBe(100);
  });

  it("extent returns min/max and pads a flat series", () => {
    expect(extent([3, 1, 2])).toEqual([1, 3]);
    expect(extent([5, 5])).toEqual([4, 6]);
    expect(extent([])).toEqual([0, 1]);
  });

  it("niceTicks produces rounded ascending ticks within range", () => {
    const ticks = niceTicks(0, 10, 4);
    expect(ticks[0]).toBeLessThanOrEqual(10);
    expect([...ticks].sort((a, b) => a - b)).toEqual(ticks);
  });
});
