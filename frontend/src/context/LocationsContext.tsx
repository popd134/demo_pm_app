/**
 * Locations context (WBS 1.4.5).
 *
 * Holds the fetched locations, the active location, and the set selected for
 * comparison. Selection persists to localStorage. A server-backed preferences store
 * replaces the local persistence in WBS 1.6.1.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { getLocations, type Location } from "../lib/api";

type Status = "loading" | "ready" | "error";

interface LocationsContextValue {
  locations: Location[];
  status: Status;
  activeId: number | null;
  compareIds: number[];
  activeLocation: Location | null;
  setActive: (id: number) => void;
  toggleCompare: (id: number) => void;
  refresh: () => void;
}

const STORAGE_KEY = "weather-dashboard-locations";
const LocationsContext = createContext<LocationsContextValue | null>(null);

interface Persisted {
  activeId: number | null;
  compareIds: number[];
}

function readPersisted(): Persisted {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Persisted;
  } catch {
    // ignore malformed storage
  }
  return { activeId: null, compareIds: [] };
}

export function LocationsProvider({ children }: { children: ReactNode }) {
  const [locations, setLocations] = useState<Location[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [activeId, setActiveId] = useState<number | null>(null);
  const [compareIds, setCompareIds] = useState<number[]>([]);

  const load = useCallback(() => {
    setStatus("loading");
    getLocations()
      .then((locs) => {
        setLocations(locs);
        const persisted = readPersisted();
        const valid = new Set(locs.map((l) => l.id));
        const active =
          persisted.activeId && valid.has(persisted.activeId)
            ? persisted.activeId
            : (locs[0]?.id ?? null);
        const compare = persisted.compareIds.filter((id) => valid.has(id));
        setActiveId(active);
        setCompareIds(compare.length > 0 ? compare : active ? [active] : []);
        setStatus("ready");
      })
      .catch(() => setStatus("error"));
  }, []);

  useEffect(() => load(), [load]);

  useEffect(() => {
    if (status === "ready") {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ activeId, compareIds }));
    }
  }, [activeId, compareIds, status]);

  const setActive = useCallback((id: number) => {
    setActiveId(id);
    setCompareIds((current) => (current.includes(id) ? current : [...current, id]));
  }, []);

  const toggleCompare = useCallback((id: number) => {
    setCompareIds((current) =>
      current.includes(id) ? current.filter((x) => x !== id) : [...current, id],
    );
  }, []);

  const activeLocation = useMemo(
    () => locations.find((l) => l.id === activeId) ?? null,
    [locations, activeId],
  );

  const value = useMemo(
    () => ({
      locations,
      status,
      activeId,
      compareIds,
      activeLocation,
      setActive,
      toggleCompare,
      refresh: load,
    }),
    [locations, status, activeId, compareIds, activeLocation, setActive, toggleCompare, load],
  );

  return <LocationsContext.Provider value={value}>{children}</LocationsContext.Provider>;
}

export function useLocations(): LocationsContextValue {
  const ctx = useContext(LocationsContext);
  if (ctx === null) {
    throw new Error("useLocations must be used within a LocationsProvider");
  }
  return ctx;
}
