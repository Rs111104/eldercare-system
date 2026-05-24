"""
Security utilities for token and password management
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
from typing import Optional
from urllib.parse import quote, unquote

from pydantic import BaseModel

from app.config import settings
try:
    from passlib.context import CryptContext
    _HAS_PASSLIB = True
except Exception:
    _HAS_PASSLIB = False

from datetime import timedelta
import json
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
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "user_id": user_id,
        "phone_number": phone_number,
        "user_type": user_type,
        "exp": int(expire.timestamp()),
    }

    import json
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac_new(settings.JWT_SECRET.encode("utf-8"), payload_json.encode("utf-8"), sha256).hexdigest()
    return f"{quote(payload_json)}.{signature}"


def create_refresh_token(user_id: str) -> str:
    # simple opaque token; server will track rotation
    return str(uuid4())

def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode JWT token"""
    try:
        import json

        encoded_payload, signature = token.rsplit(".", 1)
        payload_json = unquote(encoded_payload)
        expected = hmac_new(settings.JWT_SECRET.encode("utf-8"), payload_json.encode("utf-8"), sha256).hexdigest()
        if not compare_digest(signature, expected):
            return None

        payload = json.loads(payload_json)
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            return None

        user_id = payload.get("user_id")
        phone_number = payload.get("phone_number")
        user_type = payload.get("user_type")
        if user_id is None or phone_number is None:
            return None

        return TokenData(user_id=user_id, phone_number=phone_number, user_type=user_type, exp=datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc))
    except Exception:
        return None

def hash_password(password: str) -> str:
    """Hash password using bcrypt via passlib when available, otherwise fallback to salted sha256."""
    if _HAS_PASSLIB:
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    # fallback
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
    return compare_digest(hash_password(plain_password), hashed_password)
