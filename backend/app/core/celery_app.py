from __future__ import annotations

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger("app.celery")

_celery = None


def get_celery():
    global _celery
    if _celery is not None:
        return _celery
    broker = settings.REDIS_URL or "redis://localhost:6379/0"
    try:
        from celery import Celery

        _celery = Celery("eldercare", broker=broker, backend=broker)
        # simple config
        _celery.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")
        # schedule: release pending payouts every 15 minutes
        try:
            _celery.conf.beat_schedule = {
                'release-pending-payouts': {
                    'task': 'eldercare.release_pending_payouts',
                    'schedule': 60 * 15,
                },
            }
        except Exception:
            pass
        return _celery
    except Exception as e:
        logger.warning("Celery not available: %s", e)
        _celery = None
        return None
