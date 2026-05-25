from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from app.db import get_session, create_tables
from app.models.sql_models import Base, User, WhatsAppMessage, RefreshToken
from app.models.sql_models import Task, Tracking, Payout, PricingConfig
from app.config import settings
from app.core.security import hash_password, verify_password

logger = logging.getLogger("app.store_db")

# create tables if DB configured
create_tables(Base)


class DBStore:
    def __init__(self):
        self.Session = get_session()

    def _now(self) -> str:
        from datetime import datetime

        return datetime.utcnow().isoformat()

    def create_customer(self, phone: str, name: str, address: str = "", lat: Optional[float] = None, lng: Optional[float] = None, password: str = "") -> Dict[str, Any]:
        session = self.Session()
        user_id = str(uuid4())
        u = User(id=user_id, phone=phone, name=name, password_hash=hash_password(password) if password else "", user_type="customer", extra={"address": address, "lat": lat, "lng": lng})
        session.add(u)
        session.commit()
        session.refresh(u)
        session.close()
        return {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"}

    def create_task(self, customer_id: str, service_type: str, description: str, urgency: float, base_price: float, distance_km: float, worker_id: Optional[str] = None, voice_note_url: Optional[str] = None, status: str = "created", title: str = "Service Request") -> Dict[str, Any]:
        session = self.Session()
        task_id = str(uuid4())
        urgency_multiplier = max(1.0, min(float(urgency), 1.5))

        # Attempt to replicate InMemoryStore pricing breakdown logic using DB data
        # Get pricing config if available
        cfg = session.query(PricingConfig).filter(PricingConfig.service_type == service_type).first()
        if cfg:
            cfg_base = float(getattr(cfg, "base_price", 100.0))
            cfg_per_km = float(getattr(cfg, "per_km_rate", 5.0))
        else:
            cfg_base = float(base_price or 100.0)
            cfg_per_km = 5.0

        # Active tasks and verified workers approximations
        active_tasks = session.query(Task).filter(Task.status.in_("created", "assigned", "accepted", "in_progress")).count()
        # Count verified, unfrozen workers similar to InMemoryStore logic
        worker_rows = session.query(User).filter(User.user_type == "worker").all()
        verified_workers = len([w for w in worker_rows if (getattr(w, "extra", {}) or {}).get("is_verified") and not (getattr(w, "extra", {}) or {}).get("is_frozen")]) or 1
        busy_ratio = float(active_tasks) / max(1, verified_workers)
        surge_multiplier = 1.2 if busy_ratio >= 0.8 else 1.0

        now = datetime.utcnow()
        evening_weekend = now.weekday() >= 5 or 18 <= now.hour < 22
        time_multiplier = 1.1 if evening_weekend else 1.0

        loyalty_multiplier = 1.0
        loyalty_task_count = session.query(Task).filter(Task.customer_id == customer_id).count() if customer_id else 0
        if loyalty_task_count >= 25:
            loyalty_multiplier = 0.85
        elif loyalty_task_count >= 10:
            loyalty_multiplier = 0.90

        same_day_multiplier = 1.0

        raw_total = (cfg_base + (float(distance_km) * cfg_per_km)) * urgency_multiplier
        total = raw_total * surge_multiplier * time_multiplier * loyalty_multiplier * same_day_multiplier
        # floor/ceiling (use DB config if present, else reasonable defaults)
        floor_price = float(getattr(cfg, "floor_price", None) or max(0.0, cfg_base * 0.75))
        ceiling_price = float(getattr(cfg, "ceiling_price", None) or (cfg_base * 4.0))
        total = min(max(total, floor_price), ceiling_price)
        price = round(total, 2)

        t = Task(id=task_id, title=title, customer_id=customer_id, worker_id=worker_id, service_type=service_type, status=status, description=description, price=price, urgency=urgency_multiplier)
        session.add(t)
        session.commit()
        session.refresh(t)
        session.close()
        return {k: v for k, v in t.__dict__.items() if k != "_sa_instance_state"}

    def list_tasks(self, customer_id: Optional[str] = None, worker_id: Optional[str] = None, status: Optional[str] = None) -> list:
        session = self.Session()
        q = session.query(Task)
        if customer_id is not None:
            q = q.filter(Task.customer_id == customer_id)
        if worker_id is not None:
            q = q.filter(Task.worker_id == worker_id)
        if status is not None:
            q = q.filter(Task.status == status)
        rows = q.all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"} for row in rows]

    def update_task(self, task_id: str, **updates: Any) -> Dict[str, Any]:
        session = self.Session()
        t = session.query(Task).filter(Task.id == task_id).first()
        if not t:
            session.close()
            raise KeyError("Task not found")
        for k, v in updates.items():
            setattr(t, k, v)
        session.commit()
        session.refresh(t)
        session.close()
        return {k: v for k, v in t.__dict__.items() if k != "_sa_instance_state"}

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        session = self.Session()
        u = session.query(User).filter(User.id == customer_id, User.user_type == 'customer').first()
        session.close()
        return {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"} if u else None

    def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        session = self.Session()
        u = session.query(User).filter(User.id == worker_id, User.user_type == 'worker').first()
        session.close()
        return {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"} if u else None

    def list_workers(self) -> list:
        session = self.Session()
        rows = session.query(User).filter(User.user_type == 'worker').all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"} for row in rows]

    def list_customers(self) -> list:
        session = self.Session()
        rows = session.query(User).filter(User.user_type == 'customer').all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"} for row in rows]

    def assign_worker(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        return self.update_task(task_id, worker_id=worker_id, status='assigned')

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        from datetime import datetime
        return self.update_task(task_id, status='completed', completed_at=datetime.utcnow().isoformat())

    def cancel_task(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        return self.update_task(task_id, status='cancelled', cancellation_reason=reason)

    def record_tracking(self, task_id: str, worker_id: str, lat: float, lng: float, event_type: str = "location_update") -> Dict[str, Any]:
        session = self.Session()
        entry = Tracking(id=str(uuid4()), task_id=task_id, worker_id=worker_id, lat=lat, lng=lng, event_type=event_type, timestamp=self._now())
        session.add(entry)
        session.commit()
        session.refresh(entry)
        session.close()
        return {k: v for k, v in entry.__dict__.items() if k != "_sa_instance_state"}

    def get_latest_location(self, task_id: str):
        session = self.Session()
        entry = session.query(Tracking).filter(Tracking.task_id == task_id).order_by(Tracking.timestamp.desc()).first()
        session.close()
        return {k: v for k, v in entry.__dict__.items() if k != "_sa_instance_state"} if entry else None

    def get_tracking_for_task(self, task_id: str):
        session = self.Session()
        rows = session.query(Tracking).filter(Tracking.task_id == task_id).all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"} for row in rows]

    def upsert_pricing_config(self, service_type: str, base_price: float, per_km_rate: float) -> Dict[str, Any]:
        session = self.Session()
        row = session.query(PricingConfig).filter(PricingConfig.service_type == service_type).first()
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        if row:
            row.base_price = base_price
            row.per_km_rate = per_km_rate
            row.updated_at = now
        else:
            row = PricingConfig(id=str(uuid4()), service_type=service_type, base_price=base_price, per_km_rate=per_km_rate, updated_at=now)
            session.add(row)
        session.commit()
        session.refresh(row)
        session.close()
        return {k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"}

    def get_pricing_config(self, service_type: str):
        session = self.Session()
        row = session.query(PricingConfig).filter(PricingConfig.service_type == service_type).first()
        session.close()
        return {k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"} if row else None

    def list_pricing_config(self):
        session = self.Session()
        rows = session.query(PricingConfig).all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"} for row in rows]

    def record_payout_split(self, worker_id: str, task_id: str, amount: float):
        session = self.Session()
        immediate = round(amount * 0.75, 2)
        verification = round(amount * 0.25, 2)
        created_at = self._now()
        verification_available_at = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
        payout_rows = []
        try:
            for split_type, split_amount, status in (("immediate", immediate, "released"), ("verification", verification, "pending")):
                payout_id = str(uuid4())
                p = Payout(
                    id=payout_id,
                    worker_id=worker_id,
                    task_id=task_id,
                    amount=split_amount,
                    split_type=split_type,
                    status=status,
                    created_at=created_at,
                    verification_available_at=verification_available_at if split_type == "verification" else created_at,
                    released_at=(self._now() if split_type == "immediate" else None),
                )
                session.add(p)
                payout_rows.append(p)
            session.commit()
            result = [{k: v for k, v in p.__dict__.items() if k != "_sa_instance_state"} for p in payout_rows]
            session.close()
            return result
        except Exception as e:
            # On DB commit failure, write to a failed payouts queue on disk for retry
            logger.exception("Failed to record payout split, queueing for retry: %s", str(e))
            try:
                import os
                qpath = os.path.join(os.path.dirname(__file__), "..", "..", "failed_payouts.json")
                qpath = os.path.abspath(qpath)
                item = {
                    "worker_id": worker_id,
                    "task_id": task_id,
                    "amount": amount,
                    "created_at": created_at,
                }
                # load existing
                if os.path.exists(qpath):
                    with open(qpath, "r", encoding="utf-8") as f:
                        data = json.load(f) or []
                else:
                    data = []
                data.append(item)
                with open(qpath, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            except Exception:
                logger.exception("Failed to write failed payout to queue file")
            try:
                session.close()
            except Exception:
                pass
            return []

    def get_payouts_for_worker(self, worker_id: str):
        session = self.Session()
        rows = session.query(Payout).filter(Payout.worker_id == worker_id).all()
        session.close()
        return [{k: v for k, v in row.__dict__.items() if k != "_sa_instance_state"} for row in rows]

    def get_earnings_for_worker(self, worker_id: str):
        payouts = self.get_payouts_for_worker(worker_id)
        immediate = sum(item["amount"] for item in payouts if item["split_type"] == "immediate")
        verification = sum(item["amount"] for item in payouts if item["split_type"] == "verification" and item.get("status") == "released")
        pending = sum(item["amount"] for item in payouts if item["split_type"] == "verification" and item.get("status") != "released")
        return {"immediate": round(immediate, 2), "verification": round(verification, 2), "pending": round(pending, 2), "total": round(immediate + verification, 2)}

    def release_verification_payouts(self) -> None:
        session = self.Session()
        rows = session.query(Payout).filter(Payout.split_type == "verification", Payout.status != "released").all()
        now = datetime.now(timezone.utc)
        for payout in rows:
            available_at = getattr(payout, "verification_available_at", None)
            if not available_at:
                created_at = getattr(payout, "created_at", self._now())
                available_at = (datetime.fromisoformat(created_at) + timedelta(hours=48)).isoformat()
                payout.verification_available_at = available_at
            if datetime.fromisoformat(available_at) > now:
                continue
            payout.status = "released"
            payout.released_at = self._now()
        session.commit()
        session.close()

    def process_pending_payout_retries(self) -> None:
        # For DB store, attempt to release pending verification payouts
        try:
            self.release_verification_payouts()
        except Exception:
            logger.exception("Error releasing verification payouts")

        # Attempt to reprocess any failed_payouts.json queue
        try:
            import os
            qpath = os.path.join(os.path.dirname(__file__), "..", "..", "failed_payouts.json")
            qpath = os.path.abspath(qpath)
            if not os.path.exists(qpath):
                return
            with open(qpath, "r", encoding="utf-8") as f:
                data = json.load(f) or []
            remaining = []
            for item in data:
                try:
                    self.record_payout_split(item["worker_id"], item["task_id"], float(item.get("amount", 0)))
                except Exception:
                    logger.exception("Retrying failed payout failed for task=%s", item.get("task_id"))
                    remaining.append(item)
            if remaining:
                with open(qpath, "w", encoding="utf-8") as f:
                    json.dump(remaining, f)
            else:
                try:
                    os.remove(qpath)
                except Exception:
                    pass
        except Exception:
            logger.exception("Error processing failed payouts queue")

    def create_admin(self, phone: str, name: str, password: str = "") -> Dict[str, Any]:
        session = self.Session()
        user_id = str(uuid4())
        u = User(id=user_id, phone=phone, name=name, password_hash=hash_password(password) if password else "", user_type="admin")
        session.add(u)
        session.commit()
        session.refresh(u)
        session.close()
        return {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"}

    def has_admins(self) -> bool:
        session = self.Session()
        exists = session.query(User.id).filter(User.user_type == "admin").first() is not None
        session.close()
        return exists

    def has_any_admin(self) -> bool:
        return self.has_admins()

    def create_worker(self, phone: str, name: str, service_type: str, rating: float = 4.8, is_verified: bool = False, current_lat: Optional[float] = None, current_lng: Optional[float] = None, password: str = "") -> Dict[str, Any]:
        session = self.Session()
        user_id = str(uuid4())
        extra = {"service_type": service_type, "rating": rating, "is_verified": is_verified, "current_lat": current_lat, "current_lng": current_lng}
        u = User(id=user_id, phone=phone, name=name, password_hash=hash_password(password) if password else "", user_type="worker", extra=extra)
        session.add(u)
        session.commit()
        session.refresh(u)
        session.close()
        return {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"}

    def authenticate(self, phone: str, password: str) -> Optional[Dict[str, Any]]:
        session = self.Session()
        u = session.query(User).filter(User.phone == phone).first()
        session.close()
        if not u:
            return None
        if not u.password_hash or verify_password(password, u.password_hash):
            record = {k: v for k, v in u.__dict__.items() if k != "_sa_instance_state" and k != "password_hash"}
            return {"role": u.user_type, "record": record}
        return None

    def store_refresh_token(self, token: str, user_id: str, expires_at: str, role: Optional[str] = None) -> None:
        session = self.Session()
        rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at, role=role)
        session.add(rt)
        session.commit()
        session.close()

    def revoke_refresh_token(self, token: str) -> None:
        session = self.Session()
        session.query(RefreshToken).filter(RefreshToken.token == token).delete()
        session.commit()
        session.close()

    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        session = self.Session()
        rt = session.query(RefreshToken).filter(RefreshToken.token == token).first()
        session.close()
        if not rt:
            return None
        return {"user_id": rt.user_id, "expires_at": rt.expires_at, "role": getattr(rt, "role", None)}

    def record_login_attempt(self, phone: str, max_attempts: int = 5, window_minutes: int = 10, lock_minutes: int = 30) -> None:
        # For DB-backed store we'd still prefer Redis for rate limiting; raise to fallback logic
        raise NotImplementedError("DBStore.record_login_attempt should use Redis; ensure REDIS_URL set")

    def reset_login_attempts(self, phone: str) -> None:
        # Reset in Redis directly
        try:
            from app.core.redis_client import get_redis

            r = get_redis()
            if r:
                r.delete(f"login:{phone}:count")
                r.delete(f"login:{phone}:locked")
        except Exception:
            pass

    def store_whatsapp_message(self, phone: str, direction: str, message_type: str, content: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        session = self.Session()
        msg_id = str(uuid4())
        m = WhatsAppMessage(id=msg_id, phone=phone, direction=direction, message_type=message_type, content=content, task_id=task_id, processed=False, timestamp=self._now())
        session.add(m)
        session.commit()
        session.refresh(m)
        session.close()
        return {k: v for k, v in m.__dict__.items() if k != "_sa_instance_state"}


# Export a store instance if DB configured
_store = None
if settings.DATABASE_URL:
    try:
        _store = DBStore()
    except Exception:
        _store = None

*** End Patch