from fastapi import APIRouter
from app.core.redis_client import get_redis

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
