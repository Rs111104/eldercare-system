from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.store import store
from app.core.deps import require_role
from app.config import settings
from app.core.audit import append_audit
from app.services.admin_intelligence import AdminIntelligenceService

router = APIRouter()


class RuntimeSettingsUpdate(BaseModel):
    platform_fee_percentage: float | None = None
    authenticated_rate_limit_per_minute: int | None = None
    unauthenticated_rate_limit_per_minute: int | None = None


@router.get("/stats/overview")
async def get_system_stats(_admin=Depends(require_role("admin"))):
    customers = getattr(store, "customers", {})
    workers = getattr(store, "workers", {})
    tasks = getattr(store, "tasks", {})
    payouts = getattr(store, "payouts", {})
    return {
        "total_customers": len(customers),
        "total_workers": len(workers),
        "verified_workers": len([worker for worker in workers.values() if worker["is_verified"]]),
        "total_tasks": len(tasks),
        "completed_tasks": len([task for task in tasks.values() if task["status"] == "completed"]),
        "total_payouts": len(payouts),
        "total_revenue": round(sum(task["price"] for task in tasks.values()), 2),
        "average_rating": round(sum(worker["rating"] for worker in workers.values()) / len(workers), 2) if workers else 0,
    }


@router.get("/stats/tasks")
async def get_task_statistics(days: int = 7, _admin=Depends(require_role("admin"))):
    return {"period_days": days, "created": len(store.tasks), "assigned": len([task for task in store.tasks.values() if task["status"] == "assigned"]), "accepted": len([task for task in store.tasks.values() if task["status"] == "accepted"]), "in_progress": len([task for task in store.tasks.values() if task["status"] == "in_progress"]), "completed": len([task for task in store.tasks.values() if task["status"] == "completed"]), "cancelled": len([task for task in store.tasks.values() if task["status"] == "cancelled"])}


@router.get("/stats/workers")
async def get_worker_statistics(_admin=Depends(require_role("admin"))):
    verified = [worker for worker in store.workers.values() if worker["is_verified"]]
    return {"total_workers": len(store.workers), "verified_workers": len(verified), "pending_verification": len(store.workers) - len(verified), "total_tasks_completed": len([task for task in store.tasks.values() if task["status"] == "completed"]), "average_rating": round(sum(worker["rating"] for worker in store.workers.values()) / len(store.workers), 2) if store.workers else 0}


@router.get("/stats/revenue")
async def get_revenue_statistics(days: int = 30, _admin=Depends(require_role("admin"))):
    return {"period_days": days, "total_revenue": round(sum(task["price"] for task in store.tasks.values()), 2), "immediate_payouts": round(sum(payout["amount"] for payout in store.payouts.values() if payout["split_type"] == "immediate"), 2), "pending_verification": round(sum(payout["amount"] for payout in store.payouts.values() if payout["split_type"] == "verification" and payout["status"] != "released"), 2), "completed_payouts": round(sum(payout["amount"] for payout in store.payouts.values() if payout["split_type"] == "verification" and payout["status"] == "released"), 2)}


@router.get("/tasks/detailed")
async def get_detailed_tasks(status: str | None = None, limit: int = 50, _admin=Depends(require_role("admin"))):
    tasks = list(store.tasks.values())
    if status:
        tasks = [task for task in tasks if task["status"] == status]
    tasks.sort(key=lambda task: task["created_at"], reverse=True)
    return tasks[:limit]


@router.post("/pricing-config/{service_type}")
async def update_pricing_config(service_type: str, base_price: float, distance_charge: float, effort_multiplier: float = 1.0, _admin=Depends(require_role("admin"))):
    return store.upsert_pricing_config(service_type, base_price, distance_charge)


@router.get("/dashboard")
async def get_admin_dashboard(_admin=Depends(require_role("admin"))):
    tasks = list(getattr(store, "tasks", {}).values())
    intelligence = AdminIntelligenceService()
    return {
        "stats": await get_system_stats(_admin),
        "recent_tasks": (await get_detailed_tasks(limit=10, _admin=_admin)),
        "verified_workers": [worker for worker in store.list_workers() if worker["is_verified"]],
        "active_tasks": [task for task in tasks if task.get("status") in {"created", "assigned", "accepted", "in_progress"}],
        "pending_matches": [task for task in tasks if task.get("lifecycle_status") == "REQUESTED"],
        "held_payouts": [payout for payout in getattr(store, "payouts", {}).values() if payout.get("status") in {"pending", "held"}],
        "flagged_issues": list(getattr(store, "flagged_items", [])),
        "dead_letters": list(getattr(store, "dead_letters", [])),
        "anomalies": [anomaly.__dict__ for anomaly in intelligence.detect_anomalies(store)],
        "weekly_digest": intelligence.weekly_digest(store),
    }


@router.post("/intelligence/anomalies/run")
async def run_anomaly_detection(_admin=Depends(require_role("admin"))):
    flagged = AdminIntelligenceService().flag_anomalies(store)
    return {"flagged": flagged, "count": len(flagged)}


@router.get("/intelligence/weekly-digest")
async def get_weekly_ops_digest(_admin=Depends(require_role("admin"))):
    return AdminIntelligenceService().weekly_digest(store)


@router.get("/dead-letters")
async def list_dead_letters(_admin=Depends(require_role("admin"))):
    return {"items": list(getattr(store, "dead_letters", []))}


@router.post("/dead-letters/{dead_letter_id}/discard")
async def discard_dead_letter(dead_letter_id: str, reason: str, _admin=Depends(require_role("admin"))):
    for item in getattr(store, "dead_letters", []):
        if item["id"] == dead_letter_id:
            before = dict(item)
            item["status"] = "discarded"
            item["discard_reason"] = reason
            append_audit(store, actor_id=getattr(_admin, "user_id", ""), role="admin", action="dead_letter.discard", target_type="dead_letter", target_id=dead_letter_id, before=before, after=item, reason=reason)
            return item
    return {"status": "not_found"}


@router.get("/audit-log")
async def get_audit_log(limit: int = 100, _admin=Depends(require_role("admin"))):
    return {"items": list(getattr(store, "audit_log", []))[-limit:]}


@router.put("/settings")
async def update_runtime_settings(payload: RuntimeSettingsUpdate, _admin=Depends(require_role("admin"))):
    before = {
        "platform_fee_percentage": settings.PLATFORM_FEE_PERCENTAGE,
        "authenticated_rate_limit_per_minute": settings.RATE_LIMIT_AUTHENTICATED_PER_MINUTE,
        "unauthenticated_rate_limit_per_minute": settings.RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE,
    }
    if payload.platform_fee_percentage is not None:
        settings.PLATFORM_FEE_PERCENTAGE = max(0.0, min(payload.platform_fee_percentage, 0.5))
    if payload.authenticated_rate_limit_per_minute is not None:
        settings.RATE_LIMIT_AUTHENTICATED_PER_MINUTE = max(1, payload.authenticated_rate_limit_per_minute)
    if payload.unauthenticated_rate_limit_per_minute is not None:
        settings.RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE = max(1, payload.unauthenticated_rate_limit_per_minute)
    after = {
        "platform_fee_percentage": settings.PLATFORM_FEE_PERCENTAGE,
        "authenticated_rate_limit_per_minute": settings.RATE_LIMIT_AUTHENTICATED_PER_MINUTE,
        "unauthenticated_rate_limit_per_minute": settings.RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE,
    }
    append_audit(store, actor_id=getattr(_admin, "user_id", ""), role="admin", action="settings.update", target_type="settings", target_id="runtime", before=before, after=after, reason="admin_update")
    store.runtime_settings["platform_fee_percentage"] = settings.PLATFORM_FEE_PERCENTAGE
    store.runtime_settings["rate_limits"] = {
        "authenticated_per_minute": settings.RATE_LIMIT_AUTHENTICATED_PER_MINUTE,
        "unauthenticated_per_minute": settings.RATE_LIMIT_UNAUTHENTICATED_PER_MINUTE,
    }
    return after
