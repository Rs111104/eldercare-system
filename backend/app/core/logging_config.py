from __future__ import annotations

import logging
from typing import Any

from app.core.request_context import current_log_context


PII_KEYS = {"phone", "phone_number", "address", "content", "description", "message", "health", "notes"}


class SafeContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in current_log_context().items():
            if not hasattr(record, key):
                setattr(record, key, value)
        for key in ("status", "duration_ms"):
            if not hasattr(record, key):
                setattr(record, key, "")
        return True


class RedactingJsonFormatter(logging.Formatter):
    def __init__(self):
        super().__init__()
        from pythonjsonlogger import jsonlogger

        self._formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s %(role)s %(action)s %(duration_ms)s %(status)s"
        )

    def format(self, record: logging.LogRecord) -> str:
        self._redact(record)
        return self._formatter.format(record)

    def _redact(self, record: logging.LogRecord) -> None:
        for key in list(record.__dict__):
            if key.lower() in PII_KEYS:
                setattr(record, key, "[REDACTED]")
        if isinstance(record.msg, str) and any(token in record.msg.lower() for token in PII_KEYS):
            record.msg = "[REDACTED]"
            record.args = ()


def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # remove default handlers
    for h in list(root.handlers):
        root.removeHandler(h)
    try:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingJsonFormatter())
        handler.addFilter(SafeContextFilter())
        root.addHandler(handler)
    except Exception:
        # fallback to simple formatting
        handler = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(fmt)
        root.addHandler(handler)


# configure at import time if desired
configure_logging()
