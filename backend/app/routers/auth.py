from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone

from app.models import AuthRegisterRequest, LoginRequest, TokenResponse
from app.store import store
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.utils import sanitize_text
from app.core.deps import security

router = APIRouter()


def _has_admins() -> bool:
    checker = getattr(store, "has_any_admin", None)
    if callable(checker):
        return bool(checker())
    checker = getattr(store, "has_admins", None)
    if callable(checker):
        return bool(checker())
    admins = getattr(store, "admins", None)
    return bool(admins)


def _verify_bootstrap_token(bootstrap_token: str | None) -> None:
    if settings.ADMIN_BOOTSTRAP_TOKEN is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin bootstrap token is not configured")
    if not bootstrap_token or bootstrap_token != settings.ADMIN_BOOTSTRAP_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _require_admin_access(credentials: HTTPAuthorizationCredentials | None) -> None:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        user = get_current_user(credentials)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if getattr(user, "user_type", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _issue_response(user_type: str, user: dict) -> dict:
    access = create_access_token(user_id=user["id"], phone_number=user["phone"], user_type=user_type)
    refresh = create_refresh_token(user_id=user["id"], role=user_type)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)).isoformat()
    store.store_refresh_token(refresh, user_id=user["id"], expires_at=expires_at, role=user_type)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user_id=user["id"],
        user_type=user_type,
        user=user,
    ).model_dump()


@router.post("/register/customer")
async def register_customer(payload: AuthRegisterRequest):
    user = store.create_customer(
        phone=sanitize_text(payload.phone),
        name=sanitize_text(payload.name) or "Customer",
        address=sanitize_text(payload.address),
        lat=payload.lat,
        lng=payload.lng,
        password=payload.password,
    )
    return _issue_response("customer", user)


@router.post("/register/worker")
async def register_worker(payload: AuthRegisterRequest):
    service_type = payload.service_type or (payload.service_types[0] if payload.service_types else "help")
    user = store.create_worker(
        phone=sanitize_text(payload.phone),
        name=sanitize_text(payload.name) or "Worker",
        service_type=sanitize_text(service_type),
        rating=payload.rating,
        is_verified=payload.is_verified,
        current_lat=payload.current_lat,
        current_lng=payload.current_lng,
        password=payload.password,
    )
    return _issue_response("worker", user)


@router.post("/register/admin")
async def register_admin(
    payload: AuthRegisterRequest,
    bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
    credentials: HTTPAuthorizationCredentials | None = Security(security),
):
    """Register a new admin (separate from customers)"""
    if _has_admins():
        _require_admin_access(credentials)
    else:
        _verify_bootstrap_token(bootstrap_token)

    user = store.create_admin(
        phone=sanitize_text(payload.phone),
        name=sanitize_text(payload.name) or "Admin",
        password=payload.password,
    )
    return _issue_response("admin", user)


@router.post("/login")
async def login(payload: LoginRequest):
    # Rate limiting per phone
    try:
        store.record_login_attempt(payload.phone, max_attempts=settings.RATE_LIMIT_LOGIN_MAX, window_minutes=settings.RATE_LIMIT_LOGIN_WINDOW_MINUTES, lock_minutes=settings.RATE_LIMIT_LOCK_MINUTES)
    except Exception:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts. Try later.")

    auth = store.authenticate(payload.phone, payload.password)
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid phone or password")

    # success — reset attempts
    store.reset_login_attempts(payload.phone)
    return _issue_response(auth["role"], auth["record"])


@router.get("/me")
async def me(user=Depends(get_current_user)):
    record = store.get_customer(user.user_id) or store.get_worker(user.user_id)
    if not record and getattr(user, "user_type", None) == "admin":
        record = next((dict(admin, password_hash=None) for admin in getattr(store, "admins", {}).values() if admin["id"] == user.user_id), None)
        if record:
            record.pop("password_hash", None)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"user_id": user.user_id, "user_type": user.user_type, "user": record}


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    info = store.validate_refresh_token(refresh_token)
    if not info:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    # rotate
    store.revoke_refresh_token(refresh_token)
    # use stored role if available
    role = info.get("role") or "customer"
    new_refresh = create_refresh_token(user_id=info["user_id"], role=role)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)).isoformat()
    store.store_refresh_token(new_refresh, user_id=info["user_id"], expires_at=expires_at, role=role)

    # issue new access token
    # find user by id
    # find user and type
    user = store.get_customer(info["user_id"]) or store.get_worker(info["user_id"]) or ({"id": info["user_id"], "phone": ""})
    access = create_access_token(user_id=user["id"], phone_number=user.get("phone", ""), user_type=role)
    return {"access_token": access, "refresh_token": new_refresh}
