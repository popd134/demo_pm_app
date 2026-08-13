import { useEffect, useState } from "react";
import { Spinner } from "../ui";
import { CurrentConditions } from "./CurrentConditions";
import { getCurrentConditions, type Location, type Observation } from "../../lib/api";

type Status = "loading" | "ready" | "empty" | "error";

/**
 * Fetches and renders current conditions for a single location (WBS 1.4.3/1.4.5).
 * Used both for the active location and each compared location.
 */
export function CurrentConditionsCard({
  location,
  compact = false,
}: {
  location: Location;
  compact?: boolean;
}) {
  const [observation, setObservation] = useState<Observation | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    getCurrentConditions(location.id)
      .then((obs) => {
        if (cancelled) return;
        setObservation(obs);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        // A 404 means the location has no stored observations yet.
        const status404 =
          typeof err === "object" && err !== null && "status" in err
            ? (err as { status: number }).status === 404
            : false;
        setStatus(status404 ? "empty" : "error");
      });
    return () => {
      cancelled = true;
    };
  }, [location.id]);

  if (status === "loading") return <Spinner label="Loading…" />;
  if (status === "error") return <p className="section-subtle">Could not reach the API.</p>;
  if (status === "empty" || !observation) {
    return (
      <p className="section-subtle">
        No observations for {location.name} yet.
      </p>
    );
  }

  if (compact) {
    return (
      <div>
        <strong>{location.name}</strong>
        <div style={{ fontSize: "var(--font-xl)", fontWeight: 700 }}>
          {observation.temperature_c === null ? "—" : observation.temperature_c.toFixed(0)}°C
        </div>
        <div className="section-subtle">{observation.condition ?? "—"}</div>
      </div>
    );
  }

  return <CurrentConditions location={location} observation={observation} />;
}
