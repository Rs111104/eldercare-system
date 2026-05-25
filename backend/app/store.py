from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import radians, sin, cos, sqrt, atan2
from app.utils.geo import haversine
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.security import hash_password, verify_password, create_access_token
from app.core.redis_client import get_redis
import json


DEFAULT_PRICING = {
    "medicine": {"base_price": 120.0, "per_km_rate": 5.0},
    "help": {"base_price": 150.0, "per_km_rate": 5.0},
    "visit": {"base_price": 100.0, "per_km_rate": 5.0},
    "cleaning": {"base_price": 200.0, "per_km_rate": 5.0},
    "other": {"base_price": 130.0, "per_km_rate": 5.0},
}


def seed_default_pricing(target_store: Any, overwrite: bool = False) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for service_type, values in DEFAULT_PRICING.items():
        if not overwrite and target_store.get_pricing_config(service_type):
            continue
        target_store.upsert_pricing_config(service_type, values["base_price"], values["per_km_rate"])
        if hasattr(target_store, "pricing_config") and service_type in target_store.pricing_config:
            target_store.pricing_config[service_type]["updated_at"] = now


@dataclass
class InMemoryStore:
    customers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    admins: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    workers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tracking: List[Dict[str, Any]] = field(default_factory=list)
    payouts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    reviews: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pricing_config: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    whatsapp_messages: List[Dict[str, Any]] = field(default_factory=list)
    pending_payout_retries: List[Dict[str, Any]] = field(default_factory=list)
    matching_decisions: List[Dict[str, Any]] = field(default_factory=list)
    flagged_items: List[Dict[str, Any]] = field(default_factory=list)
    trusted_contacts: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    auth_tokens: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    refresh_tokens: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    auth_attempts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    lock: Lock = field(default_factory=Lock)

    def reset(self) -> None:
        with self.lock:
            self.customers.clear()
            self.admins.clear()
            self.workers.clear()
            self.tasks.clear()
            self.tracking.clear()
            self.payouts.clear()
            self.reviews.clear()
            self.pricing_config.clear()
            self.whatsapp_messages.clear()
            self.pending_payout_retries.clear()
            self.matching_decisions.clear()
            self.flagged_items.clear()
            self.trusted_contacts.clear()
            self.auth_tokens.clear()
            self.refresh_tokens.clear()
            self.auth_attempts.clear()
            seed_default_pricing(self, overwrite=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # Use shared haversine utility from app.utils.geo

    def create_customer(self, phone: str, name: str, address: str = "", lat: Optional[float] = None, lng: Optional[float] = None, password: str = "") -> Dict[str, Any]:
        with self.lock:
            customer_id = str(uuid4())
            customer = {
                "id": customer_id,
                "phone": phone,
                "name": name,
                "address": address,
                "lat": lat,
                "lng": lng,
                "password_hash": hash_password(password) if password else "",
                "created_at": self._now(),
                "trusted_contacts": [],
            }
            self.customers[customer_id] = customer
            return self._public_customer(customer)

    def create_admin(self, phone: str, name: str, password: str = "") -> Dict[str, Any]:
        with self.lock:
            admin_id = str(uuid4())
            admin = {
                "id": admin_id,
                "phone": phone,
                "name": name,
                "password_hash": hash_password(password) if password else "",
                "created_at": self._now(),
            }
            self.admins[admin_id] = admin
            return {k: v for k, v in admin.items() if k != "password_hash"}

    def has_admins(self) -> bool:
        return bool(self.admins)

    def has_any_admin(self) -> bool:
        return self.has_admins()

    def create_worker(self, phone: str, name: str, service_type: str, rating: float = 4.8, is_verified: bool = False, current_lat: Optional[float] = None, current_lng: Optional[float] = None, password: str = "") -> Dict[str, Any]:
        with self.lock:
            worker_id = str(uuid4())
            is_flagged = float(rating) < 3.0
            flag_reason = "Low rating requires manual review" if is_flagged else ""
            worker = {
                "id": worker_id,
                "phone": phone,
                "name": name,
                "service_type": service_type,
                "rating": float(rating),
                "is_verified": is_verified,
                "current_lat": current_lat,
                "current_lng": current_lng,
                "acceptance_rate": 0.85,
                "experience_years": 2.0,
                "completed_tasks": 0,
                "is_flagged": is_flagged,
                "flag_reason": flag_reason,
                "is_frozen": False,
                "password_hash": hash_password(password) if password else "",
                "documents": [],
                "created_at": self._now(),
            }
            self.workers[worker_id] = worker
            if is_flagged:
                self._flag_item("worker", worker_id, flag_reason)
            return self._public_worker(worker)

    def authenticate(self, phone: str, password: str) -> Optional[Dict[str, Any]]:
        # Admins have highest precedence
        for admin in self.admins.values():
            if admin["phone"] == phone and (not admin["password_hash"] or verify_password(password, admin["password_hash"])):
                return {"role": "admin", "record": {k: v for k, v in admin.items() if k != "password_hash"}}
        for customer in self.customers.values():
            if customer["phone"] == phone and (not customer["password_hash"] or verify_password(password, customer["password_hash"])):
                return {"role": "customer", "record": self._public_customer(customer)}
        for worker in self.workers.values():
            if worker["phone"] == phone and (not worker["password_hash"] or verify_password(password, worker["password_hash"])):
                return {"role": "worker", "record": self._public_worker(worker)}
        return None

    def issue_token(self, user_id: str, phone: str, role: str) -> str:
        token = create_access_token(user_id=user_id, phone_number=phone, user_type=role)
        self.auth_tokens[token] = {"user_id": user_id, "phone": phone, "role": role, "created_at": self._now()}
        return token

    def store_refresh_token(self, token: str, user_id: str, expires_at: str, role: Optional[str] = None) -> None:
        r = get_redis()
        if r:
            key = f"refresh:{token}"
            payload = {"user_id": user_id, "expires_at": expires_at, "role": role}
            # set with expiry
            try:
                # calculate ttl
                from datetime import datetime
                expires = datetime.fromisoformat(expires_at)
                ttl = int((expires - datetime.now(tz=expires.tzinfo)).total_seconds())
                r.set(key, json.dumps(payload), ex=max(1, ttl))
                return
            except Exception:
                pass
        with self.lock:
            self.refresh_tokens[token] = {"user_id": user_id, "expires_at": expires_at, "role": role}

    def revoke_refresh_token(self, token: str) -> None:
        r = get_redis()
        if r:
            try:
                r.delete(f"refresh:{token}")
                return
            except Exception:
                pass
        with self.lock:
            if token in self.refresh_tokens:
                del self.refresh_tokens[token]

    def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        r = get_redis()
        if r:
            try:
                raw = r.get(f"refresh:{token}")
                if not raw:
                    return None
                info = json.loads(raw)
                from datetime import datetime
                expires = datetime.fromisoformat(info["expires_at"])
                if expires < datetime.now(timezone.utc):
                    r.delete(f"refresh:{token}")
                    return None
                return {"user_id": info.get("user_id"), "expires_at": info.get("expires_at"), "role": info.get("role")}
            except Exception:
                pass
        info = self.refresh_tokens.get(token)
        if not info:
            return None
        try:
            expires = datetime.fromisoformat(info["expires_at"])
            if expires < datetime.now(timezone.utc):
                # expired
                with self.lock:
                    del self.refresh_tokens[token]
                return None
            return {"user_id": info.get("user_id"), "expires_at": info.get("expires_at"), "role": info.get("role")}
        except Exception:
            return None

    def record_login_attempt(self, phone: str, max_attempts: int = 5, window_minutes: int = 10, lock_minutes: int = 30) -> None:
        r = get_redis()
        if r:
            try:
                key_count = f"login:{phone}:count"
                key_lock = f"login:{phone}:locked"
                if r.exists(key_lock):
                    # still locked
                    raise Exception("LOCKED")
                count = r.incr(key_count)
                if count == 1:
                    r.expire(key_count, window_minutes * 60)
                if count > max_attempts:
                    r.setex(key_lock, lock_minutes * 60, "1")
                    raise Exception("LOCKED")
                return
            except Exception:
                raise

        now = datetime.now(timezone.utc)
        entry = self.auth_attempts.get(phone)
        if not entry:
            self.auth_attempts[phone] = {"count": 1, "first_at": now.isoformat(), "locked_until": None}
            return

        # check lock
        locked_until = entry.get("locked_until")
        if locked_until:
            try:
                lu = datetime.fromisoformat(locked_until)
                if lu > now:
                    raise Exception("LOCKED")
                else:
                    # clear lock
                    entry["locked_until"] = None
                    entry["count"] = 1
                    entry["first_at"] = now.isoformat()
                    return
            except Exception:
                raise

        # within window
        first_at = datetime.fromisoformat(entry["first_at"])
        if (now - first_at).total_seconds() <= window_minutes * 60:
            entry["count"] += 1
            if entry["count"] > max_attempts:
                entry["locked_until"] = (now + timedelta(minutes=lock_minutes)).isoformat()
                raise Exception("LOCKED")
        else:
            # reset window
            entry["count"] = 1
            entry["first_at"] = now.isoformat()

    def reset_login_attempts(self, phone: str) -> None:
        r = get_redis()
        if r:
            try:
                r.delete(f"login:{phone}:count")
                r.delete(f"login:{phone}:locked")
                return
            except Exception:
                pass
        if phone in self.auth_attempts:
            del self.auth_attempts[phone]

    def create_task(self, customer_id: str, service_type: str, description: str, urgency: float, base_price: float, distance_km: float, worker_id: Optional[str] = None, voice_note_url: Optional[str] = None, status: str = "created", title: str = "Service Request", same_day_bundle: bool = False) -> Dict[str, Any]:
        with self.lock:
            task_id = str(uuid4())
            urgency_multiplier = max(1.0, min(float(urgency), 1.5))
            pricing = self.calculate_pricing_breakdown(service_type, distance_km, urgency_multiplier, customer_id=customer_id, same_day_bundle=same_day_bundle)
            price = float(pricing["total_price"])
            is_flagged = price >= 5000 or urgency_multiplier >= 1.45
            flag_reason = "High value or urgent task requires review" if is_flagged else ""
            task = {
                "id": task_id,
                "title": title,
                "customer_id": customer_id,
                "worker_id": worker_id,
                "service_type": service_type,
                "task_type": service_type,
                "status": status,
                "description": description,
                "price": price,
                "urgency": urgency_multiplier,
                "urgency_level": int(round(1 + ((urgency_multiplier - 1.0) / 0.125))) if urgency_multiplier >= 1.0 else 1,
                "voice_note_url": voice_note_url,
                "same_day_bundle": same_day_bundle,
                "pricing_breakdown": pricing["pricing_breakdown"],
                "created_at": self._now(),
                "completed_at": None,
                "arrival_confirmed": False,
                "is_flagged": is_flagged,
                "flag_reason": flag_reason,
            }
            self.tasks[task_id] = task
            if is_flagged:
                self._flag_item("task", task_id, flag_reason)
            return self._public_task(task)

    def update_task(self, task_id: str, **updates: Any) -> Dict[str, Any]:
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                raise KeyError("Task not found")
            task.update(updates)
            return self._public_task(task)

    def list_tasks(self, customer_id: Optional[str] = None, worker_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        tasks = list(self.tasks.values())
        if customer_id is not None:
            tasks = [task for task in tasks if task["customer_id"] == customer_id]
        if worker_id is not None:
            tasks = [task for task in tasks if task.get("worker_id") == worker_id]
        if status is not None:
            tasks = [task for task in tasks if task["status"] == status]
        tasks.sort(key=lambda task: task["created_at"], reverse=True)
        return [self._public_task(task) for task in tasks]

    def assign_worker(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError("Task not found")
        task["arrival_confirmed"] = False
        task["worker_id"] = worker_id
        task["assigned_worker_id"] = worker_id
        task["status"] = "assigned"
        return self._public_task(task)

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError("Task not found")
        task["status"] = "completed"
        task["completed_at"] = self._now()
        worker_id = task.get("worker_id") or task.get("assigned_worker_id")
        if worker_id and worker_id in self.workers:
            self.workers[worker_id]["completed_tasks"] = int(self.workers[worker_id].get("completed_tasks", 0)) + 1
        return self._public_task(task)

    def cancel_task(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError("Task not found")
        task["status"] = "cancelled"
        task["cancellation_reason"] = reason
        return self._public_task(task)

    def record_tracking(self, task_id: str, worker_id: str, lat: float, lng: float, event_type: str = "location_update") -> Dict[str, Any]:
        entry = {
            "id": str(uuid4()),
            "task_id": task_id,
            "worker_id": worker_id,
            "lat": lat,
            "lng": lng,
            "event_type": event_type,
            "timestamp": self._now(),
        }
        self.tracking.append(entry)
        return entry

    def set_trusted_contacts(self, customer_id: str, contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self.trusted_contacts[customer_id] = [
            {"name": sanitize.get("name", ""), "phone": sanitize.get("phone", "")} for sanitize in contacts if sanitize.get("phone")
        ]
        if customer_id in self.customers:
            self.customers[customer_id]["trusted_contacts"] = list(self.trusted_contacts[customer_id])
        return list(self.trusted_contacts[customer_id])

    def get_worker_badge_tier(self, worker_id: str) -> str:
        worker = self.workers.get(worker_id)
        if not worker:
            return "Bronze"
        rating = float(worker.get("rating", 0))
        completed = int(worker.get("completed_tasks", 0))
        if rating >= 4.7 and completed >= 25:
            return "Gold"
        if rating >= 4.3 and completed >= 10:
            return "Silver"
        return "Bronze"

    def confirm_arrival(self, task_id: str, worker_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError("Task not found")
        task["arrival_confirmed"] = True
        task["arrival_confirmed_at"] = self._now()
        task["status"] = "in_progress"
        return self._public_task(task)

    def send_sos_alert(self, task_id: str, customer_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        customer = self.customers.get(customer_id)
        alert = {
            "id": str(uuid4()),
            "task_id": task_id,
            "customer_id": customer_id,
            "created_at": self._now(),
            "type": "sos",
        }
        contacts = list(self.trusted_contacts.get(customer_id, []))
        if customer and customer.get("trusted_contacts"):
            contacts.extend(customer.get("trusted_contacts", []))
        if task and task.get("worker_id") and task["worker_id"] in self.workers:
            worker = self.workers[task["worker_id"]]
            alert["worker_id"] = worker["id"]
            alert["worker_phone"] = worker["phone"]
        for contact in contacts:
            if contact.get("phone"):
                self.store_whatsapp_message(phone=contact["phone"], direction="out", message_type="text", content=f"SOS alert for customer {customer_id} on task {task_id}. Please check immediately.")
        for admin in self.admins.values():
            self.store_whatsapp_message(phone=admin["phone"], direction="out", message_type="text", content=f"SOS alert raised for customer {customer_id} on task {task_id}.")
        return alert

    def freeze_worker(self, worker_id: str, reason: str) -> Dict[str, Any]:
        worker = self.workers.get(worker_id)
        if not worker:
            raise KeyError("Worker not found")
        worker["is_frozen"] = True
        worker["is_verified"] = False
        worker["is_flagged"] = True
        worker["flag_reason"] = reason
        for admin in self.admins.values():
            self.store_whatsapp_message(phone=admin["phone"], direction="out", message_type="text", content=f"Worker {worker_id} frozen: {reason}")
        return self._public_worker(worker)

    def get_latest_location(self, task_id: str) -> Optional[Dict[str, Any]]:
        entries = [item for item in self.tracking if item["task_id"] == task_id]
        return entries[-1] if entries else None

    def get_tracking_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        return [item for item in self.tracking if item["task_id"] == task_id]

    def record_payout_split(self, worker_id: str, task_id: str, amount: float) -> List[Dict[str, Any]]:
        with self.lock:
            immediate = round(amount * 0.75, 2)
            verification = round(amount * 0.25, 2)
            created_at = self._now()
            verification_available_at = (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat()
            is_flagged = amount >= 10000
            flag_reason = "Large payout requires manual review" if is_flagged else ""
            payout_rows = []
            for split_type, split_amount, status in (("immediate", immediate, "released"), ("verification", verification, "pending")):
                payout_id = str(uuid4())
                payout = {
                    "id": payout_id,
                    "worker_id": worker_id,
                    "task_id": task_id,
                    "amount": split_amount,
                    "split_type": split_type,
                    "status": status,
                    "created_at": created_at,
                    "verification_available_at": verification_available_at if split_type == "verification" else created_at,
                    "released_at": created_at if split_type == "immediate" else None,
                    "is_flagged": is_flagged,
                    "flag_reason": flag_reason,
                }
                self.payouts[payout_id] = payout
                payout_rows.append(payout)
            if is_flagged:
                self._flag_item("payout", task_id, flag_reason)
            return payout_rows

    def get_payouts_for_worker(self, worker_id: str) -> List[Dict[str, Any]]:
        return [payout for payout in self.payouts.values() if payout["worker_id"] == worker_id]

    def get_earnings_for_worker(self, worker_id: str) -> Dict[str, float]:
        payouts = self.get_payouts_for_worker(worker_id)
        immediate = sum(item["amount"] for item in payouts if item["split_type"] == "immediate")
        verification = sum(item["amount"] for item in payouts if item["split_type"] == "verification" and item["status"] == "released")
        pending = sum(item["amount"] for item in payouts if item["split_type"] == "verification" and item["status"] != "released")
        return {"immediate": round(immediate, 2), "verification": round(verification, 2), "pending": round(pending, 2), "total": round(immediate + verification, 2)}

    def _flag_item(self, record_type: str, record_id: str, reason: str) -> Dict[str, Any]:
        entry = {
            "id": str(uuid4()),
            "record_type": record_type,
            "record_id": record_id,
            "reason": reason,
            "created_at": self._now(),
        }
        self.flagged_items.append(entry)
        for admin in self.admins.values():
            try:
                self.store_whatsapp_message(
                    phone=admin["phone"],
                    direction="out",
                    message_type="text",
                    content=f"Review needed for {record_type} {record_id}: {reason}",
                )
            except Exception:
                pass
        return entry

    def release_verification_payouts(self) -> None:
        now = datetime.now(timezone.utc)
        for payout in list(self.payouts.values()):
            if payout["split_type"] == "verification" and payout.get("status") != "released":
                try:
                    available_at = payout.get("verification_available_at")
                    if not available_at:
                        available_at = (datetime.fromisoformat(payout.get("created_at", self._now())) + timedelta(hours=48)).isoformat()
                        payout["verification_available_at"] = available_at
                    if datetime.fromisoformat(available_at) > now:
                        continue
                    # Placeholder for external payout release API call.
                    payout["status"] = "released"
                    payout["released_at"] = self._now()
                except Exception:
                    # Log and queue for retry
                    payout_id = payout.get("id")
                    self.pending_payout_retries.append({"payout_id": payout_id, "attempted_at": self._now()})

    def process_pending_payout_retries(self) -> None:
        # Attempt to reprocess queued payout releases
        retry_queue = list(self.pending_payout_retries)
        self.pending_payout_retries.clear()
        for item in retry_queue:
            payout_id = item.get("payout_id")
            payout = self.payouts.get(payout_id)
            if not payout:
                continue
            try:
                payout["status"] = "released"
                payout["released_at"] = self._now()
            except Exception:
                # If it still fails, re-queue with timestamp
                self.pending_payout_retries.append({"payout_id": payout_id, "attempted_at": self._now()})

    def store_whatsapp_message(self, phone: str, direction: str, message_type: str, content: str, task_id: Optional[str] = None) -> Dict[str, Any]:
        message = {
            "id": str(uuid4()),
            "phone": phone,
            "direction": direction,
            "message_type": message_type,
            "content": content,
            "task_id": task_id,
            "processed": False,
            "timestamp": self._now(),
        }
        # push to Redis queue if available for durable processing
        r = get_redis()
        if r:
            try:
                # push to both a list and a stream for compatibility and better processing
                r.lpush("whatsapp:queue", json.dumps(message))
                # streams require string fields; store payload as json under 'data'
                try:
                    r.xadd("whatsapp:stream", {"data": json.dumps(message)})
                except Exception:
                    # older redis clients or permissions may fail; ignore
                    pass
            except Exception:
                pass
        self.whatsapp_messages.append(message)
        return message

    def find_nearest_workers(self, lat: float, lng: float, service_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        max_radius_km = 5.0
        expanded_radius_km = max_radius_km
        candidates: List[Dict[str, Any]] = []

        while expanded_radius_km <= 40.0 and not candidates:
            lat_delta = expanded_radius_km / 111.0
            lng_delta = expanded_radius_km / max(1.0, 111.0 * max(abs(cos(radians(lat))), 0.01))
            bbox_min_lat = lat - lat_delta
            bbox_max_lat = lat + lat_delta
            bbox_min_lng = lng - lng_delta
            bbox_max_lng = lng + lng_delta

            for worker in self.workers.values():
                if not worker.get("is_verified"):
                    continue
                if worker.get("service_type") != service_type:
                    continue

                worker_lat = worker.get("current_lat")
                worker_lng = worker.get("current_lng")
                if worker_lat is None or worker_lng is None:
                    continue
                if not (bbox_min_lat <= float(worker_lat) <= bbox_max_lat and bbox_min_lng <= float(worker_lng) <= bbox_max_lng):
                    continue

                distance = haversine(lat, lng, float(worker_lat), float(worker_lng))
                if distance > expanded_radius_km:
                    continue

                rating = float(worker.get("rating", 4.8))
                proximity_score = max(0.0, 1.0 - min(distance / expanded_radius_km, 1.0))
                acceptance_score = max(0.0, min(float(worker.get("acceptance_rate", 0.85)), 1.0))
                experience_score = max(0.0, min(float(worker.get("completed_tasks", 0)) / 50.0, 1.0))
                rating_score = max(0.0, min(rating / 5.0, 1.0))
                match_score = round((0.4 * rating_score) + (0.3 * proximity_score) + (0.2 * acceptance_score) + (0.1 * experience_score), 4)

                candidates.append({
                    **self._public_worker(worker),
                    "distance_km": round(distance, 2),
                    "match_score": match_score,
                    "match_factors": {
                        "rating": round(rating_score, 4),
                        "proximity": round(proximity_score, 4),
                        "acceptance_rate": round(acceptance_score, 4),
                        "experience": round(experience_score, 4),
                    },
                })

            if not candidates:
                expanded_radius_km *= 2.0

        if not candidates:
            self.matching_decisions.append({
                "service_type": service_type,
                "lat": lat,
                "lng": lng,
                "radius_km": expanded_radius_km,
                "candidate_count": 0,
                "created_at": self._now(),
            })
            for admin in self.admins.values():
                self.store_whatsapp_message(
                    phone=admin["phone"],
                    direction="out",
                    message_type="text",
                    content=f"No verified worker matched a {service_type} request near {lat:.4f}, {lng:.4f}. Please review the queue.",
                )
            return []

        candidates.sort(key=lambda item: (-item["match_score"], item["distance_km"], -item["rating"]))
        selected = candidates[:limit]
        self.matching_decisions.append({
            "service_type": service_type,
            "lat": lat,
            "lng": lng,
            "radius_km": expanded_radius_km,
            "candidate_count": len(candidates),
            "selected_worker_ids": [worker["id"] for worker in selected],
            "created_at": self._now(),
        })
        return selected

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        customer = self.customers.get(customer_id)
        return self._public_customer(customer) if customer else None

    def get_worker(self, worker_id: str) -> Optional[Dict[str, Any]]:
        worker = self.workers.get(worker_id)
        return self._public_worker(worker) if worker else None

    def list_customers(self) -> List[Dict[str, Any]]:
        return [self._public_customer(customer) for customer in self.customers.values()]

    def list_workers(self) -> List[Dict[str, Any]]:
        return [self._public_worker(worker) for worker in self.workers.values()]

    def upsert_pricing_config(self, service_type: str, base_price: float, per_km_rate: float, floor_price: Optional[float] = None, ceiling_price: Optional[float] = None) -> Dict[str, Any]:
        row = self.pricing_config.get(service_type)
        now = self._now()
        if row:
            row.update({"base_price": base_price, "per_km_rate": per_km_rate, "floor_price": floor_price, "ceiling_price": ceiling_price, "updated_at": now})
        else:
            row = {"id": str(uuid4()), "service_type": service_type, "base_price": base_price, "per_km_rate": per_km_rate, "floor_price": floor_price, "ceiling_price": ceiling_price, "updated_at": now}
            self.pricing_config[service_type] = row
        return dict(row)

    def get_pricing_config(self, service_type: str) -> Optional[Dict[str, Any]]:
        row = self.pricing_config.get(service_type)
        return dict(row) if row else None

    def calculate_pricing_breakdown(self, service_type: str, distance_km: float, urgency: float, customer_id: Optional[str] = None, same_day_bundle: bool = False) -> Dict[str, Any]:
        config = self.get_pricing_config(service_type) or self.get_pricing_config("other") or {"base_price": 100.0, "per_km_rate": 5.0}
        base_price = float(config.get("base_price", 100.0))
        per_km_rate = float(config.get("per_km_rate", 5.0))
        urgency_multiplier = max(1.0, min(float(urgency), 1.5))

        active_tasks = len([task for task in self.tasks.values() if task["status"] in {"created", "assigned", "accepted", "in_progress"}])
        verified_workers = len([worker for worker in self.workers.values() if worker.get("is_verified") and not worker.get("is_frozen")]) or 1
        busy_ratio = active_tasks / verified_workers
        surge_multiplier = 1.2 if busy_ratio >= 0.8 else 1.0

        now = datetime.now().astimezone()
        evening_weekend = now.weekday() >= 5 or 18 <= now.hour < 22
        time_multiplier = 1.1 if evening_weekend else 1.0

        loyalty_multiplier = 1.0
        loyalty_task_count = 0
        if customer_id:
            loyalty_task_count = len([task for task in self.tasks.values() if task["customer_id"] == customer_id])
            if loyalty_task_count >= 25:
                loyalty_multiplier = 0.85
            elif loyalty_task_count >= 10:
                loyalty_multiplier = 0.90

        same_day_multiplier = 0.85 if same_day_bundle else 1.0
        floor_price = float(config.get("floor_price") or max(0.0, base_price * 0.75))
        ceiling_price = float(config.get("ceiling_price") or (base_price * 4.0))

        raw_total = (base_price + (distance_km * per_km_rate)) * urgency_multiplier
        total = raw_total * surge_multiplier * time_multiplier * loyalty_multiplier * same_day_multiplier
        total = min(max(total, floor_price), ceiling_price)

        return {
            "service_type": service_type,
            "base_price": round(base_price, 2),
            "distance_km": round(distance_km, 2),
            "distance_charge_per_km": round(per_km_rate, 2),
            "urgency": round(urgency_multiplier, 2),
            "urgency_multiplier": round(urgency_multiplier, 2),
            "surge_multiplier": round(surge_multiplier, 2),
            "time_multiplier": round(time_multiplier, 2),
            "loyalty_multiplier": round(loyalty_multiplier, 2),
            "same_day_multiplier": round(same_day_multiplier, 2),
            "busy_ratio": round(busy_ratio, 2),
            "loyalty_task_count": loyalty_task_count,
            "floor_price": round(floor_price, 2),
            "ceiling_price": round(ceiling_price, 2),
            "pricing_breakdown": {
                "base": round(base_price, 2),
                "distance": round(distance_km * per_km_rate, 2),
                "urgency": round((base_price + (distance_km * per_km_rate)) * (urgency_multiplier - 1.0), 2),
                "surge": round(raw_total * (surge_multiplier - 1.0), 2),
                "time": round(raw_total * surge_multiplier * (time_multiplier - 1.0), 2),
                "loyalty": round(raw_total * surge_multiplier * time_multiplier * (1.0 - loyalty_multiplier), 2),
                "same_day": round(raw_total * surge_multiplier * time_multiplier * loyalty_multiplier * (1.0 - same_day_multiplier), 2),
            },
            "total_price": round(total, 2),
        }

    def list_pricing_config(self) -> List[Dict[str, Any]]:
        return [dict(row) for row in self.pricing_config.values()]

    def _public_customer(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in customer.items() if key != "password_hash"}

    def _public_worker(self, worker: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in worker.items() if key != "password_hash"}

    def _public_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        public = dict(task)
        return public


store = InMemoryStore()
# NOTE: Do not call `store.reset()` at import time — reset() should only be
# invoked manually in tests or explicit maintenance scripts. Calling reset on
# startup caused unintended data wipes during application boot.
if os.environ.get("USE_DB_STORE", "").lower() in {"1", "true", "yes"}:
    try:
        from app.store_db import _store as db_store

        if db_store is not None:
            store = db_store
    except Exception:
        # keep in-memory store as default
        pass
