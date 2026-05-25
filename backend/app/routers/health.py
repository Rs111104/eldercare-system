import asyncio
import time

from fastapi import APIRouter
from app.core.redis_client import get_redis
from app.config import settings
from app.db import get_engine

router = APIRouter()


@router.get("/healthz")
async def healthz():
    r = get_redis()
    redis_ok = False
    try:
        if r:
            r.ping()
            redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok", "redis": redis_ok}


@router.get("/health/deep")
async def deep_health():
    started = time.perf_counter()

    def check_redis():
        r = get_redis()
        if not r:
            return {"ok": False, "configured": bool(settings.REDIS_URL)}
        r.ping()
        return {"ok": True, "configured": True}

    def check_db():
        engine = get_engine()
        if not engine:
            return {"ok": True, "configured": False}
        with engine.connect() as conn:
            conn.exec_driver_sql("select 1")
        return {"ok": True, "configured": True}

    def check_external(name: str, configured: bool):
        return {"ok": bool(configured), "configured": bool(configured), "skipped": not configured, "name": name}

    async def run_check(name: str, fn):
        try:
            return name, await asyncio.wait_for(asyncio.to_thread(fn), timeout=0.15)
        except Exception as exc:
            return name, {"ok": False, "error": exc.__class__.__name__}

    checks = dict(await asyncio.gather(
        run_check("redis", check_redis),
        run_check("db", check_db),
        run_check("whatsapp", lambda: check_external("whatsapp", bool(settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID))),
        run_check("openai", lambda: check_external("openai", bool(settings.OPENAI_API_KEY))),
    ))

    duration_ms = int((time.perf_counter() - started) * 1000)
    status = "ok" if all(item.get("ok") or item.get("skipped") for item in checks.values()) else "degraded"
    return {"status": status, "duration_ms": duration_ms, "checks": checks}
