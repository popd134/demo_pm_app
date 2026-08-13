import { useEffect, useState } from "react";
import { Button, ErrorState, SkeletonLines } from "../ui";
import { useQuery } from "../../hooks/useQuery";
import { api, type Preferences } from "../../lib/api";
import { invalidateQueries } from "../../lib/queryCache";
import "./settings.css";

interface ThresholdField {
  metric: string;
  label: string;
  bounds: ("min" | "max")[];
}

const THRESHOLD_FIELDS: ThresholdField[] = [
  { metric: "temperature_c", label: "Temperature (°C)", bounds: ["min", "max"] },
  { metric: "precipitation_mm", label: "Precipitation (mm)", bounds: ["max"] },
  { metric: "wind_speed_ms", label: "Wind speed (m/s)", bounds: ["max"] },
];

type ThresholdDraft = Record<string, Record<string, string>>;

function toDraft(prefs: Preferences): ThresholdDraft {
  const draft: ThresholdDraft = {};
  for (const field of THRESHOLD_FIELDS) {
    draft[field.metric] = {};
    for (const bound of field.bounds) {
      const value = prefs.alert_thresholds[field.metric]?.[bound];
      draft[field.metric][bound] = value === undefined ? "" : String(value);
    }
  }
  return draft;
}

function fromDraft(draft: ThresholdDraft): Record<string, Record<string, number>> {
  const result: Record<string, Record<string, number>> = {};
  for (const [metric, bounds] of Object.entries(draft)) {
    const parsed: Record<string, number> = {};
    for (const [bound, raw] of Object.entries(bounds)) {
      if (raw.trim() !== "" && !Number.isNaN(Number(raw))) {
        parsed[bound] = Number(raw);
      }
    }
    if (Object.keys(parsed).length > 0) result[metric] = parsed;
  }
  return result;
}

/** Manage preferred units and alert thresholds, wired to the preferences API (WBS 1.6.2). */
export function PreferencesForm() {
  const { data, isLoading, isError, refetch } = useQuery<Preferences>(
    "preferences",
    () => api.preferences.get(),
    { staleTime: 60_000 },
  );

  const [tempUnit, setTempUnit] = useState("c");
  const [windUnit, setWindUnit] = useState("ms");
  const [thresholds, setThresholds] = useState<ThresholdDraft>({});
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (data) {
      setTempUnit(data.temperature_unit);
      setWindUnit(data.wind_unit);
      setThresholds(toDraft(data));
    }
  }, [data]);

  async function handleSave() {
    setBusy(true);
    setSaved(false);
    try {
      await api.preferences.update({
        temperature_unit: tempUnit,
        wind_unit: windUnit,
        alert_thresholds: fromDraft(thresholds),
      });
      invalidateQueries((k) => k === "preferences");
      setSaved(true);
    } finally {
      setBusy(false);
    }
  }

  if (isLoading) return <SkeletonLines lines={4} />;
  if (isError) return <ErrorState message="Could not load preferences." onRetry={refetch} />;

  return (
    <div className="settings-form">
      <div className="settings-row">
        <label className="settings-field">
          <span>Temperature unit</span>
          <select value={tempUnit} onChange={(e) => setTempUnit(e.target.value)}>
            <option value="c">Celsius (°C)</option>
            <option value="f">Fahrenheit (°F)</option>
          </select>
        </label>
        <label className="settings-field">
          <span>Wind unit</span>
          <select value={windUnit} onChange={(e) => setWindUnit(e.target.value)}>
            <option value="ms">m/s</option>
            <option value="kmh">km/h</option>
            <option value="mph">mph</option>
          </select>
        </label>
      </div>

      <h4 className="settings-subheading">Alert thresholds</h4>
      <p className="section-subtle">
        Leave a field blank to use the system default for that bound.
      </p>
      {THRESHOLD_FIELDS.map((field) => (
        <div key={field.metric} className="settings-row">
          <span className="settings-metric-label">{field.label}</span>
          {field.bounds.map((bound) => (
            <label key={bound} className="settings-field settings-field--inline">
              <span>{bound}</span>
              <input
                type="number"
                value={thresholds[field.metric]?.[bound] ?? ""}
                onChange={(e) =>
                  setThresholds((prev) => ({
                    ...prev,
                    [field.metric]: { ...prev[field.metric], [bound]: e.target.value },
                  }))
                }
              />
            </label>
          ))}
        </div>
      ))}

      <div className="settings-actions">
        <Button onClick={handleSave} disabled={busy}>
          {busy ? "Saving…" : "Save preferences"}
        </Button>
        {saved && <span className="settings-saved">Saved ✓</span>}
      </div>
    </div>
  );
}
