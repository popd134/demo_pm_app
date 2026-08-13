import { useState } from "react";
import { Button, EmptyState, ErrorState, SkeletonLines } from "../ui";
import { useQuery } from "../../hooks/useQuery";
import { useLocations } from "../../context/LocationsContext";
import { api, type SavedLocation } from "../../lib/api";
import { invalidateQueries } from "../../lib/queryCache";
import "./settings.css";

const KEY = "saved-locations";

/** Manage the user's saved locations, wired to the preferences API (WBS 1.6.2). */
export function SavedLocationsManager() {
  const { locations } = useLocations();
  const { data, isLoading, isError, refetch } = useQuery<SavedLocation[]>(
    KEY,
    () => api.preferences.listSaved(),
    { staleTime: 30_000 },
  );
  const [selected, setSelected] = useState<string>("");

  const savedIds = new Set((data ?? []).map((s) => s.location.id));
  const addable = locations.filter((l) => !savedIds.has(l.id));

  async function add() {
    if (!selected) return;
    await api.preferences.addSaved(Number(selected));
    setSelected("");
    invalidateQueries((k) => k === KEY);
    refetch();
  }

  async function remove(locationId: number) {
    await api.preferences.removeSaved(locationId);
    invalidateQueries((k) => k === KEY);
    refetch();
  }

  if (isLoading) return <SkeletonLines lines={3} />;
  if (isError) return <ErrorState message="Could not load saved locations." onRetry={refetch} />;

  return (
    <div className="settings-form">
      <div className="settings-row">
        <select
          className="settings-select"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          aria-label="Choose a location to save"
        >
          <option value="">Choose a location…</option>
          {addable.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>
        <Button variant="secondary" onClick={add} disabled={!selected}>
          Save location
        </Button>
      </div>

      {(!data || data.length === 0) && (
        <EmptyState icon="📍" title="No saved locations" message="Add one from the list above." />
      )}

      {data && data.length > 0 && (
        <ul className="saved-list">
          {data.map((saved) => (
            <li key={saved.id} className="saved-list__item">
              <span>
                <strong>{saved.location.name}</strong>
                {saved.location.country && (
                  <span className="section-subtle"> · {saved.location.country}</span>
                )}
              </span>
              <Button variant="ghost" onClick={() => remove(saved.location.id)}>
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
