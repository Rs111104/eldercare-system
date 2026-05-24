from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from app.core.deps import get_current_user
from app.config import settings

# Load remote secrets (if configured) before any other initialization
from app.core.secrets import load_remote_secrets
load_remote_secrets()

from app.core.logging_config import configure_logging

# ensure logging configured early
configure_logging()
from app.routers import (
    admin_router,
    auth_router,
    customers_router,
    onboarding_router,
    payouts_router,
    pricing_router,
    safety_router,
    tasks_router,
    tracking_router,
    whatsapp_router,
    workers_router,
)
from app.routers.health import router as health_router
from app.routers.realtime import router as realtime_router
from app.store import store
from app.routers.whatsapp import reprocess_stored_whatsapp_messages
from app.services.queue_worker import start_queue_worker, stop_queue_worker
from app.middleware.request_logging import RequestLoggingMiddleware
from app.core import metrics


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, debug=settings.DEBUG)

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Never expose stack traces to client. Log full exception server-side.
    logger.exception("Unhandled error: %s", str(exc))
    payload = {
        "error": True,
        "code": "INTERNAL_ERROR",
        "message": "An internal error occurred",
        "timestamp": datetime.utcnow().isoformat(),
    }
    return JSONResponse(status_code=500, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Return structured errors for HTTPExceptions
    code = getattr(exc, "detail", "")
    message = str(code) if isinstance(code, str) else ""
    payload = {
        "error": True,
        "code": getattr(exc, "status_code", "HTTP_ERROR"),
        "message": message or "An error occurred",
        "timestamp": datetime.utcnow().isoformat(),
    }
    return JSONResponse(status_code=exc.status_code or 400, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = {
        "error": True,
        "code": "VALIDATION_ERROR",
        "message": "Invalid request payload",
        "details": exc.errors(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return JSONResponse(status_code=422, content=payload)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, settings.BACKEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add request logging + metrics middleware
app.add_middleware(RequestLoggingMiddleware)


@app.on_event("startup")
async def startup_event() -> None:
    store.reset()
    # Process any pending payout retries and reprocess stored whatsapp messages
    try:
        store.process_pending_payout_retries()
    except Exception:
        logger.exception("Error processing pending payout retries")

    try:
        await reprocess_stored_whatsapp_messages()
    except Exception:
        logger.exception("Error reprocessing stored whatsapp messages on startup")

    # start background queue worker for WhatsApp/payouts
    try:
        await start_queue_worker(app)
    except Exception:
        logger.exception("Failed to start queue worker")


api_prefix = settings.API_V1_STR
app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(tasks_router, prefix=f"{api_prefix}/tasks", tags=["tasks"], dependencies=[Depends(get_current_user)])
app.include_router(workers_router, prefix=f"{api_prefix}/workers", tags=["workers"], dependencies=[Depends(get_current_user)])
app.include_router(customers_router, prefix=f"{api_prefix}/customers", tags=["customers"], dependencies=[Depends(get_current_user)])
app.include_router(pricing_router, prefix=f"{api_prefix}/pricing", tags=["pricing"], dependencies=[Depends(get_current_user)])
app.include_router(whatsapp_router, prefix=f"{api_prefix}/whatsapp", tags=["whatsapp"])
app.include_router(onboarding_router, prefix=f"{api_prefix}/onboarding", tags=["onboarding"], dependencies=[Depends(get_current_user)])
app.include_router(admin_router, prefix=f"{api_prefix}/admin", tags=["admin"], dependencies=[Depends(get_current_user)])
app.include_router(tracking_router, prefix=f"{api_prefix}/tracking", tags=["tracking"], dependencies=[Depends(get_current_user)])
app.include_router(payouts_router, prefix=f"{api_prefix}/payouts", tags=["payouts"], dependencies=[Depends(get_current_user)])
app.include_router(safety_router, prefix=f"{api_prefix}/safety", tags=["safety"], dependencies=[Depends(get_current_user)])
app.include_router(health_router, prefix=f"{api_prefix}", tags=["health"])
app.include_router(realtime_router, prefix=f"{api_prefix}", tags=["realtime"])


@app.get("/")
async def root():
    return {"message": "ElderCare Platform API", "version": settings.APP_VERSION, "docs": f"{settings.BACKEND_URL}/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.on_event("shutdown")
async def shutdown_event() -> None:
    try:
        await stop_queue_worker(app)
    except Exception:
        logger.exception("Error stopping queue worker")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

@app.get('/metrics')
async def metrics_endpoint():
    try:
        data = metrics.metrics_latest()
        from fastapi.responses import Response

        return Response(content=data, media_type=metrics.METRICS_CONTENT_TYPE)
    except Exception:
        return {"error": "prometheus_client not available"}
