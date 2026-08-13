"""Centralised structured logging (WBS 1.7.4).

Configures the root and uvicorn loggers with either a human-readable or JSON formatter
so logs can be shipped to a central store. Call :func:`setup_logging` on startup.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "context", {}).items():
            payload[key] = value
        return json.dumps(payload)


def setup_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Configure application logging once at startup."""
    handler = logging.StreamHandler()
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # Align uvicorn's loggers with our handler/level.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False
