from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging
import time
from sqlalchemy import event

logger = logging.getLogger("app.db")

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is not None:
        return _engine
    url = settings.DATABASE_URL
    if not url:
        return None
    _engine = create_engine(url, future=True, pool_size=5, max_overflow=10, pool_pre_ping=True)
    _install_query_logging(_engine)
    return _engine


def _install_query_logging(engine):
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.perf_counter()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        elapsed = time.perf_counter() - getattr(context, "_query_start_time", time.perf_counter())
        if elapsed > 2.0:
            logger.warning("slow_query", extra={"action": "db.query", "status": "slow", "duration_ms": int(elapsed * 1000), "query": statement[:1000]})


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        if engine is None:
            return None
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def create_tables(base):
    engine = get_engine()
    if engine is None:
        logger.info("No DATABASE_URL configured; skipping table creation")
        return
    base.metadata.create_all(bind=engine)
