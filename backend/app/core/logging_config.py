from __future__ import annotations

import logging


def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    # remove default handlers
    for h in list(root.handlers):
        root.removeHandler(h)
    try:
        from pythonjsonlogger import jsonlogger

        handler = logging.StreamHandler()
        fmt = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
        handler.setFormatter(fmt)
        root.addHandler(handler)
    except Exception:
        # fallback to simple formatting
        handler = logging.StreamHandler()
        fmt = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(fmt)
        root.addHandler(handler)


# configure at import time if desired
configure_logging()
