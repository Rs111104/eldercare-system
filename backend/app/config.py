from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    APP_NAME: str = "ElderCare Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    JWT_SECRET: str = Field(default="change-me")
    ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7
    RATE_LIMIT_LOGIN_MAX: int = 5
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = 10
    RATE_LIMIT_LOCK_MINUTES: int = 30

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_APP_SECRET: str = ""

    OPENAI_API_KEY: str = ""
    GOOGLE_SPEECH_API_KEY: str = ""
    GOOGLE_MAPS_API_KEY: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""

    IMMEDIATE_PAYOUT_PERCENTAGE: float = 0.75
    VERIFICATION_PAYOUT_PERCENTAGE: float = 0.25
    DEFAULT_TASK_EXPIRY_MINUTES: int = 60
    REDIS_URL: str = ""
    DATABASE_URL: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
