"""On-call alerting hooks for critical conditions (WBS 1.7.4).

Emits CRITICAL structured logs (which a log-based alerting rule can page on) and, when
``ALERT_WEBHOOK_URL`` is configured, best-effort POSTs the alert to that webhook. Used
for ingestion failures and API errors.
"""

from __future__ import annotations

import json
import logging
import urllib.request

from app.core.config import get_settings

logger = logging.getLogger("app.monitoring")


def notify_critical(event: str, **context: object) -> None:
    """Record a critical operational event and forward it to the alert webhook.

    Never raises: alerting must not take down the request path.
    """
    logger.critical(event, extra={"context": context})

    settings = get_settings()
    url = settings.alert_webhook_url
    if not url:
        return
    try:
        payload = json.dumps({"event": event, "context": context}).encode("utf-8")
        request = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(request, timeout=3)  # noqa: S310 (configured URL)
    except Exception:  # pragma: no cover - best effort
        logger.warning("failed to deliver alert to webhook", exc_info=True)
