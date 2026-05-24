from __future__ import annotations

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger("app.redis")

_redis = None


def get_redis():
    global _redis
    if _redis is not None:
        return _redis
    url = settings.REDIS_URL
    if not url:
        return None
    try:
        import redis
        _redis = redis.Redis.from_url(url, decode_responses=True)
        # quick ping
        _redis.ping()
        return _redis
    except Exception as e:
        logger.warning("Redis not available: %s", e)
        _redis = None
        return None
    