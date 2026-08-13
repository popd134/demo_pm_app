import { useLocations } from "../../context/LocationsContext";
import { LocationSearch } from "./LocationSearch";
import "./locations.css";

/**
 * Location controls (WBS 1.4.5): search to add, chips to switch the active location
 * and toggle which locations are compared.
 */
export function LocationBar() {
  const { locations, activeId, compareIds, setActive, toggleCompare } = useLocations();
  const compared = locations.filter((l) => compareIds.includes(l.id));

  return (
    <div className="location-bar">
      <LocationSearch />
      <div className="location-bar__chips">
        {compared.length === 0 && (
          <span className="section-subtle">Search to add a location.</span>
        )}
        {compared.map((loc) => (
          <span
            key={loc.id}
            className={
              "location-chip" + (loc.id === activeId ? " location-chip--active" : "")
            }
          >
            <button
              type="button"
              className="location-chip__label"
              onClick={() => setActive(loc.id)}
              aria-pressed={loc.id === activeId}
            >
              {loc.name}
            </button>
            <button
              type="button"
              className="location-chip__remove"
              aria-label={`Remove ${loc.name} from comparison`}
              onClick={() => toggleCompare(loc.id)}
            >
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
