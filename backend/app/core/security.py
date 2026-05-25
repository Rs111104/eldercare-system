"""
Security utilities for token and password management
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel
from jose import jwt, JWTError

from app.config import settings
try:
    from passlib.context import CryptContext
    _HAS_PASSLIB = True
except Exception:
    _HAS_PASSLIB = False

from datetime import timedelta
from uuid import uuid4


class TokenData(BaseModel):
    user_id: str
    phone_number: str
    user_type: str  # "customer", "worker", "admin"
    exp: datetime


def create_access_token(
    user_id: str,
    phone_number: str,
    user_type: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT token using python-jose HS256."""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "user_id": user_id,
        "phone_number": phone_number,
        "user_type": user_type,
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=getattr(settings, "ALGORITHM", "HS256"))
    return token


def create_refresh_token(user_id: str, role: str) -> str:
    # keep simple uuid:role format for refresh tokens
    return f"{uuid4()}:{role}"


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token using python-jose."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[getattr(settings, "ALGORITHM", "HS256")])
        exp = payload.get("exp")
        if not exp or int(exp) < int(datetime.now(timezone.utc).timestamp()):
            return None
        user_id = payload.get("user_id")
        phone_number = payload.get("phone_number")
        user_type = payload.get("user_type")
        if user_id is None or phone_number is None:
            return None
        return TokenData(user_id=user_id, phone_number=phone_number, user_type=user_type, exp=datetime.fromtimestamp(int(exp), tz=timezone.utc))
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt via passlib when available, otherwise fallback to salted sha256."""
    if _HAS_PASSLIB:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    # fallback
    from hashlib import sha256
    salt = settings.JWT_SECRET[:16]
    return sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against the stored digest using passlib when available, otherwise fallback."""
    if _HAS_PASSLIB:
        try:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    # fallback
    from hmac import compare_digest
    return compare_digest(hash_password(plain_password), hashed_password)
