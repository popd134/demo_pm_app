import "./widgets.css";

interface StatTileProps {
  label: string;
  value: string;
  unit?: string;
  icon?: string;
}

/** A single metric tile used in the current-conditions summary (WBS 1.4.3). */
export function StatTile({ label, value, unit, icon }: StatTileProps) {
  return (
    <div className="stat-tile">
      <div className="stat-tile__label">
        {icon && <span aria-hidden>{icon}</span>}
        {label}
      </div>
      <div className="stat-tile__value">
        {value}
        {unit && <span className="stat-tile__unit">{unit}</span>}
      </div>
    </div>
  );
}
