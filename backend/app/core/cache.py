from __future__ import annotations

import json
import functools
import logging
from typing import Callable

from fastapi import Request

from app.core.redis_client import get_redis
from app.core import metrics

logger = logging.getLogger('app.cache')


def _make_key(prefix: str, request: Request) -> str:
    # include path and sorted query params
    qs = '&'.join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
    return f"cache:{prefix}:{request.method}:{request.url.path}?{qs}"


def cache_response(ttl: int = 30):
    """Decorator to cache FastAPI endpoint responses using Redis.

    ttl: seconds to store the cached response.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, request: Request | None = None, **kwargs):
            # FastAPI will inject Request into this wrapper when available.
            # fallback: find Request in args/kwargs if not injected
            if request is None:
                for a in args:
                    if isinstance(a, Request):
                        request = a
                        break
            if request is None:
                request = kwargs.get('request')

            redis = get_redis()
            key = None
            if redis and request is not None:
                try:
                    key = _make_key(func.__name__, request)
                    cached = redis.get(key)
                    if cached:
                        try:
                            if metrics.CACHE_HITS is not None:
                                metrics.CACHE_HITS.labels(key_prefix=func.__name__).inc()
                        except Exception:
                            pass
                        return json.loads(cached)
                except Exception as e:
                    logger.debug('Cache read failed: %s', e)

            # ensure wrapped func receives the request object as a parameter
            if 'request' not in kwargs and request is not None:
                kwargs['request'] = request
            result = await func(*args, **kwargs)

            if redis and key:
                try:
                    redis.set(key, json.dumps(result), ex=ttl)
                except Exception as e:
                    logger.debug('Cache write failed: %s', e)
                else:
                    try:
                        if metrics.CACHE_MISSES is not None:
                            metrics.CACHE_MISSES.labels(key_prefix=func.__name__).inc()
                    except Exception:
                        pass
            else:
                # no redis or no key -> count as miss for observability
                try:
                    if metrics.CACHE_MISSES is not None:
                        metrics.CACHE_MISSES.labels(key_prefix=func.__name__).inc()
                except Exception:
                    pass

            return result

        return wrapper

    return decorator


def _invalidate_pattern(pattern: str) -> int:
    """Delete keys matching pattern. Returns number of keys deleted."""
    redis = get_redis()
    if not redis:
        return 0
    count = 0
    try:
        for key in redis.scan_iter(match=pattern):
            try:
                redis.delete(key)
                count += 1
            except Exception:
                logger.debug('Failed to delete cache key %s', key)
    except Exception as e:
        logger.debug('Cache invalidate scan failed: %s', e)
    return count


def invalidate_task_cache(task_id: str) -> int:
    path = f"/api/v1/tasks/{task_id}"
    # delete detail cache and available tasks listing cache
    patterns = [f"cache:*:{path}*", f"cache:*:/api/v1/tasks/available/quick*"]
    total = 0
    for p in patterns:
        total += _invalidate_pattern(p)
    try:
        if metrics.CACHE_INVALIDATIONS is not None:
            metrics.CACHE_INVALIDATIONS.inc(total)
    except Exception:
        pass
    logger.debug('Invalidated %d keys for task %s', total, task_id)
    return total


def invalidate_worker_cache(worker_id: str) -> int:
    path = f"/api/v1/workers/{worker_id}"
    patterns = [f"cache:*:{path}*", f"cache:*:/api/v1/workers/available/by-service/*"]
    total = 0
    for p in patterns:
        total += _invalidate_pattern(p)
    try:
        if metrics.CACHE_INVALIDATIONS is not None:
            metrics.CACHE_INVALIDATIONS.inc(total)
    except Exception:
        pass
    logger.debug('Invalidated %d keys for worker %s', total, worker_id)
    return total
