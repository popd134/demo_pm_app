"""Evaluate stored observations for anomalies and persist alerts (WBS 1.3.2)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.alert import Alert
from app.models.weather import Observation
from app.services import queries
from app.services.analytics import METRICS
from app.services.anomaly import (
    DEFAULT_THRESHOLDS,
    AlertEvent,
    detect_spike,
    detect_threshold_breaches,
)


def effective_thresholds(settings: Settings) -> dict[str, dict[str, float]]:
    """Merge configured overrides onto the default per-metric bounds."""
    merged = {m: dict(bounds) for m, bounds in DEFAULT_THRESHOLDS.items()}
    for metric, bounds in settings.anomaly_thresholds.items():
        merged.setdefault(metric, {}).update(bounds)
    return merged


def _reading(observation: Observation) -> dict[str, float | None]:
    return {metric: getattr(observation, metric) for metric in METRICS}


def _already_alerted(
    db: Session, location_id: int, observation_id: int | None, metric: str, kind: str
) -> bool:
    stmt = select(Alert.id).where(
        Alert.location_id == location_id,
        Alert.observation_id == observation_id,
        Alert.metric == metric,
        Alert.kind == kind,
    )
    return db.scalars(stmt).first() is not None


def evaluate_location(
    db: Session, location_id: int, settings: Settings | None = None
) -> list[Alert]:
    """Detect anomalies in a location's latest reading and persist new alerts."""
    settings = settings or get_settings()
    latest = queries.latest_observation(db, location_id)
    if latest is None:
        return []

    reading = _reading(latest)
    events: list[AlertEvent] = detect_threshold_breaches(
        reading, effective_thresholds(settings)
    )

    for metric in METRICS:
        history = [
            v
            for _, v in queries.metric_series(db, location_id, metric)
            if v is not None
        ]
        # Exclude the latest value from its own baseline.
        current = getattr(latest, metric)
        baseline = history[:-1] if history and history[-1] == current else history
        spike = detect_spike(
            metric, baseline, current, settings.anomaly_spike_sensitivity
        )
        if spike is not None:
            events.append(spike)

    created: list[Alert] = []
    for event in events:
        if _already_alerted(
            db, location_id, latest.id, event.metric, event.kind
        ):
            continue
        alert = Alert(
            location_id=location_id,
            observation_id=latest.id,
            metric=event.metric,
            value=event.value,
            threshold=event.threshold,
            kind=event.kind,
            severity=event.severity,
            message=event.message,
        )
        db.add(alert)
        created.append(alert)
    db.commit()
    for alert in created:
        db.refresh(alert)
    return created


def list_alerts(db: Session, location_id: int, limit: int = 50) -> list[Alert]:
    stmt = (
        select(Alert)
        .where(Alert.location_id == location_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
