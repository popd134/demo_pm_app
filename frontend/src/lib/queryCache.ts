/**
 * Minimal client-side query cache (WBS 1.5.2).
 *
 * A dependency-free store of server-state keyed by string, with request de-duplication,
 * staleness-based refetch, manual invalidation and change subscriptions. Consumed by
 * the `useQuery` hook; background/interval refetch is layered on in WBS 1.5.4.
 */

export type QueryStatus = "loading" | "success" | "error";

export interface QueryEntry<T = unknown> {
  data?: T;
  error?: unknown;
  updatedAt: number;
  status: QueryStatus;
  promise?: Promise<void>;
}

const store = new Map<string, QueryEntry>();
const listeners = new Map<string, Set<() => void>>();

function emit(key: string): void {
  listeners.get(key)?.forEach((fn) => fn());
}

export function subscribe(key: string, fn: () => void): () => void {
  let set = listeners.get(key);
  if (!set) {
    set = new Set();
    listeners.set(key, set);
  }
  set.add(fn);
  return () => {
    set?.delete(fn);
  };
}

export function getEntry<T>(key: string): QueryEntry<T> | undefined {
  return store.get(key) as QueryEntry<T> | undefined;
}

/** Fetch a query unless a fresh value or an in-flight request already exists. */
export function runQuery<T>(
  key: string,
  fetcher: () => Promise<T>,
  staleTime: number,
): Promise<void> {
  const existing = store.get(key);
  const isFresh =
    existing?.status === "success" && Date.now() - existing.updatedAt < staleTime;
  if (isFresh) return Promise.resolve();
  if (existing?.promise) return existing.promise;

  const promise = fetcher()
    .then((data) => {
      store.set(key, { data, updatedAt: Date.now(), status: "success" });
      emit(key);
    })
    .catch((error: unknown) => {
      const prev = store.get(key);
      store.set(key, {
        data: prev?.data,
        error,
        updatedAt: Date.now(),
        status: "error",
      });
      emit(key);
    });

  store.set(key, {
    data: existing?.data,
    updatedAt: existing?.updatedAt ?? 0,
    status: existing?.data === undefined ? "loading" : existing.status,
    promise,
  });
  emit(key);
  return promise;
}

/** Mark matching queries stale (next read/subscription refetches). */
export function invalidateQueries(predicate: (key: string) => boolean): void {
  for (const [key, entry] of store) {
    if (predicate(key)) {
      store.set(key, { ...entry, updatedAt: 0, promise: undefined });
      emit(key);
    }
  }
}

export function setQueryData<T>(key: string, data: T): void {
  store.set(key, { data, updatedAt: Date.now(), status: "success" });
  emit(key);
}

/** Test/util helper to reset the cache. */
export function clearQueryCache(): void {
  store.clear();
}
