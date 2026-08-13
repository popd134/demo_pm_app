import { useMemo, useState } from "react";
import { useLocations } from "../../context/LocationsContext";
import "./locations.css";

/** Search / autocomplete over saved locations (WBS 1.4.5). */
export function LocationSearch() {
  const { locations, setActive } = useLocations();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return locations.slice(0, 8);
    return locations
      .filter((l) => l.name.toLowerCase().includes(q) || (l.country ?? "").toLowerCase().includes(q))
      .slice(0, 8);
  }, [locations, query]);

  return (
    <div className="location-search">
      <input
        className="location-search__input"
        type="search"
        placeholder="Search locations…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setOpen(true)}
        onBlur={() => window.setTimeout(() => setOpen(false), 120)}
        aria-label="Search locations"
      />
      {open && matches.length > 0 && (
        <ul className="location-search__menu">
          {matches.map((loc) => (
            <li key={loc.id}>
              <button
                type="button"
                className="location-search__option"
                onMouseDown={() => {
                  setActive(loc.id);
                  setQuery("");
                }}
              >
                <span>{loc.name}</span>
                {loc.country && <span className="section-subtle">{loc.country}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && query.trim() && matches.length === 0 && (
        <ul className="location-search__menu">
          <li className="location-search__empty">No matches</li>
        </ul>
      )}
    </div>
  );
}
