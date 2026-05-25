from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def append_audit(store: Any, *, actor_id: str = "", role: str = "", action: str, target_type: str, target_id: str, before: dict | None = None, after: dict | None = None, reason: str = "") -> dict:
    entry = {
        "id": str(uuid4()),
        "actor_id": actor_id,
        "role": role,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "before": before or {},
        "after": after or {},
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if not hasattr(store, "audit_log"):
        setattr(store, "audit_log", [])
    store.audit_log.append(entry)
    return entry
