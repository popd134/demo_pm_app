"""In-process metrics registry (WBS 1.7.4).

A tiny counter/gauge registry with JSON and Prometheus-text exposition, so the running
service surfaces request volume, API errors and ingestion failures without pulling in a
metrics backend. Scrape ``/api/metrics/prometheus`` or read ``/api/metrics`` (JSON).
"""

from __future__ import annotations

import threading


def _label_key(labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(labels.items()))


class Metrics:
    """Thread-safe counters and gauges keyed by name + labels."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, dict[tuple, float]] = {}
        self._gauges: dict[str, float] = {}

    def inc(self, name: str, amount: float = 1.0, **labels: str) -> None:
        with self._lock:
            series = self._counters.setdefault(name, {})
            key = _label_key(labels)
            series[key] = series.get(key, 0.0) + amount

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict:
        """Return a JSON-friendly view of all metrics."""
        with self._lock:
            counters = {
                name: [
                    {"labels": dict(key), "value": value}
                    for key, value in series.items()
                ]
                for name, series in self._counters.items()
            }
            return {"counters": counters, "gauges": dict(self._gauges)}

    def prometheus(self) -> str:
        """Render metrics in the Prometheus text exposition format."""
        lines: list[str] = []
        with self._lock:
            for name, series in sorted(self._counters.items()):
                lines.append(f"# TYPE {name} counter")
                for key, value in series.items():
                    labels = ",".join(f'{k}="{v}"' for k, v in key)
                    suffix = f"{{{labels}}}" if labels else ""
                    lines.append(f"{name}{suffix} {value}")
            for name, value in sorted(self._gauges.items()):
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")
        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()


# Process-wide registry.
metrics = Metrics()
