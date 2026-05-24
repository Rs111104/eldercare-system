from __future__ import annotations

import asyncio
import random
from typing import Callable, TypeVar, Any, Coroutine

T = TypeVar("T")


def retry_async(retries: int = 3, base_delay: float = 0.5, jitter: float = 0.1):
    """Decorator for retrying async functions with exponential backoff."""
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]):
        async def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    # last attempt — re-raise for caller to handle/log
                    if attempt > retries:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    # add jitter
                    delay = delay + random.uniform(0, jitter)
                    try:
                        await asyncio.sleep(delay)
                    except Exception:
                        # preserve cancellation
                        raise
        return wrapper
    return decorator


def retry_sync(retries: int = 3, base_delay: float = 0.5, jitter: float = 0.1):
    """Retry decorator for sync functions."""
    def decorator(func: Callable[..., T]):
        def wrapper(*args, **kwargs) -> T:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception:
                    attempt += 1
                    if attempt > retries:
                        raise
                    delay = base_delay * (2 ** (attempt - 1))
                    delay = delay + random.uniform(0, jitter)
                    try:
                        asyncio.run(asyncio.sleep(delay))
                    except Exception:
                        raise
        return wrapper
    return decorator
