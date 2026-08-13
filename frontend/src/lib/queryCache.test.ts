import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  clearQueryCache,
  getEntry,
  invalidateQueries,
  runQuery,
} from "./queryCache";

describe("queryCache", () => {
  beforeEach(() => clearQueryCache());

  it("stores fetched data and dedupes concurrent requests", async () => {
    const fetcher = vi.fn(async () => 42);
    await Promise.all([
      runQuery("k", fetcher, 1000),
      runQuery("k", fetcher, 1000),
    ]);
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(getEntry<number>("k")?.data).toBe(42);
  });

  it("serves fresh data without refetching", async () => {
    const fetcher = vi.fn(async () => 1);
    await runQuery("k", fetcher, 10_000);
    await runQuery("k", fetcher, 10_000);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("refetches after invalidation", async () => {
    const fetcher = vi.fn(async () => 1);
    await runQuery("k", fetcher, 10_000);
    invalidateQueries((key) => key === "k");
    await runQuery("k", fetcher, 10_000);
    expect(fetcher).toHaveBeenCalledTimes(2);
  });

  it("records an error status on failure", async () => {
    const fetcher = vi.fn(async () => {
      throw new Error("boom");
    });
    await runQuery("bad", fetcher, 1000);
    expect(getEntry("bad")?.status).toBe("error");
  });
});
