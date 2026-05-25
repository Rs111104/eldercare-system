from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request
import time
import logging
from uuid import uuid4

from app.core import metrics
from app.config import settings
from app.core.request_context import action_var, request_id_var, role_var, user_id_var
from app.core.security import verify_token


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger('request')
        self._requests: dict[str, tuple[int, int]] = {}

    def _rate_limit(self, key: str, limit: int) -> bool:
        now = int(time.time())
        window = now // 60
        current_window, count = self._requests.get(key, (window, 0))
        if current_window != window:
            self._requests[key] = (window, 1)
            return True
        if count >= limit:
            return False
        self._requests[key] = (window, count + 1)
        return True

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        status_code = 500
        path = request.url.path
        method = request.method
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request_id_var.set(request_id)
        action_var.set(f"{request.method} {request.url.path}")
        user_id_var.set("")
        role_var.set("")
        token = request.headers.get("Authorization", "").replace("Bearer ", "", 1)
        token_data = verify_token(token) if token else None
        if token_data:
            user_id_var.set(token_data.user_id)
            role_var.set(token_data.user_type)

        try:
            client_ip = request.client.host if request.client else "unknown"
            if path not in {"/api/v1/whatsapp/webhook"} and client_ip != "testclient":
                if token_data:
                    allowed = self._rate_limit(f"user:{token_data.user_id}", settings.RATE_LIMIT_AUTHENTICATED_PER_MINUTE)
                else:
                    allowed = self._rate_limit(f"ip:{client_ip}", settings.RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE)
                if not allowed:
                    from fastapi.responses import JSONResponse

                    status_code = 429
                    response = JSONResponse(
                        status_code=429,
                        content={"error": True, "code": "RATE_LIMITED", "message": "Too many requests. Please try again shortly.", "request_id": request_id},
                    )
                    response.headers["X-Request-ID"] = request_id
                    return response
            response = await call_next(request)
            status_code = getattr(response, 'status_code', 200)
            response.headers["X-Request-ID"] = request_id
        except Exception as exc:  # ensure we still observe exceptions
            status_code = 500
            self.logger.exception("unhandled_exception")
            raise
        finally:
            elapsed = time.time() - start
            client = request.client.host if request.client else None
            extra = {
                'method': method,
                'path': path,
                'status_code': status_code,
                'status': status_code,
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
