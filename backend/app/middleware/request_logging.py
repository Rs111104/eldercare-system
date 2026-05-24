from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request
import time
import logging

from app.core import metrics


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger('request')

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
            status_code = getattr(response, 'status_code', 200)
        except Exception as exc:  # ensure we still observe exceptions
            status_code = 500
            raise
        finally:
            elapsed = time.time() - start
            path = request.url.path
            method = request.method
            client = request.client.host if request.client else None
            extra = {
                'method': method,
                'path': path,
                'status_code': status_code,
                'duration_ms': int(elapsed * 1000),
                'client': client,
            }
            try:
                # increment prometheus metrics if available
                if metrics.HTTP_REQUESTS is not None:
                    metrics.HTTP_REQUESTS.labels(method=method, endpoint=path, status=str(status_code)).inc()
                if metrics.HTTP_LATENCY is not None:
                    metrics.HTTP_LATENCY.labels(method=method, endpoint=path).observe(elapsed)
            except Exception:
                pass

            self.logger.info("request", extra=extra)

        return response
