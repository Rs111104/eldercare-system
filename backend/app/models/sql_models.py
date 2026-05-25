from __future__ import annotations

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


def now_iso():
    return datetime.utcnow().isoformat()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    user_type = Column(String, nullable=False)  # 'customer'|'worker'|'admin'
    extra = Column(JSON, nullable=True)
    created_at = Column(String, default=now_iso)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    title = Column(String)
    customer_id = Column(String)
    worker_id = Column(String)
    service_type = Column(String)
    status = Column(String)
    description = Column(Text)
    price = Column(Float)
    urgency = Column(Float)
    created_at = Column(String, default=now_iso)


class Tracking(Base):
    __tablename__ = "tracking"
    id = Column(String, primary_key=True)
    task_id = Column(String)
    worker_id = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    event_type = Column(String)
    timestamp = Column(String, default=now_iso)


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    id = Column(String, primary_key=True)
    phone = Column(String)
    direction = Column(String)
    message_type = Column(String)
    content = Column(Text)
    task_id = Column(String, nullable=True)
    processed = Column(Boolean, default=False)
    timestamp = Column(String, default=now_iso)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    token = Column(String, primary_key=True)
    user_id = Column(String, index=True)
    expires_at = Column(String)
    role = Column(String, nullable=True)


class Payout(Base):
    __tablename__ = "payouts"
    id = Column(String, primary_key=True)
    worker_id = Column(String)
    task_id = Column(String)
    amount = Column(Float)
    split_type = Column(String)
    status = Column(String)
    created_at = Column(String, default=now_iso)
    verification_available_at = Column(String, nullable=True)
    released_at = Column(String, nullable=True)


class PricingConfig(Base):
    __tablename__ = "pricing_config"
    id = Column(String, primary_key=True)
    service_type = Column(String, unique=True)
    base_price = Column(Float)
    per_km_rate = Column(Float)
    updated_at = Column(String, default=now_iso)
