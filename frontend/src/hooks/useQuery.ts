import { useEffect, useReducer } from "react";
import { getEntry, runQuery, subscribe } from "../lib/queryCache";

export interface UseQueryOptions {
  /** How long a cached value is considered fresh, in ms (default 30s). */
  staleTime?: number;
  /** Background refetch interval in ms (WBS 1.5.4). */
  refetchInterval?: number;
  /** Skip fetching while false. */
  enabled?: boolean;
}

export interface UseQueryResult<T> {
  data: T | undefined;
  error: unknown;
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
  dataUpdatedAt: number;
  refetch: () => void;
}

/**
 * Subscribe a component to a cached query (WBS 1.5.2). De-duplicates concurrent
 * requests, serves cached data instantly, and refetches when stale. The cache key
 * identifies the request, so the fetcher is deliberately excluded from effect deps.
 */
export function useQuery<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: UseQueryOptions = {},
): UseQueryResult<T> {
  const { staleTime = 30_000, refetchInterval, enabled = true } = options;
  const [, rerender] = useReducer((c: number) => c + 1, 0);

  useEffect(() => {
    if (!enabled) return;
    return subscribe(key, rerender);
  }, [key, enabled]);

  useEffect(() => {
    if (!enabled) return;
    runQuery(key, fetcher, staleTime);
    if (refetchInterval && refetchInterval > 0) {
      const id = window.setInterval(() => runQuery(key, fetcher, 0), refetchInterval);
      return () => window.clearInterval(id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, enabled, refetchInterval, staleTime]);

  const entry = getEntry<T>(key);
  const data = entry?.data;
  return {
    data,
    error: entry?.error,
    isLoading: (!entry || entry.status === "loading") && data === undefined,
    isFetching: entry?.status === "loading",
    isError: entry?.status === "error",
    dataUpdatedAt: entry?.updatedAt ?? 0,
    refetch: () => runQuery(key, fetcher, 0),
  };
}
