from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

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
    _engine = create_engine(url, future=True)
    return _engine


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
*** End Patch