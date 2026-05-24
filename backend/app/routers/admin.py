from __future__ import annotations

from fastapi import APIRouter, Depends

from app.store import store
from app.core.deps import require_role

router = APIRouter()


@router.get("/stats/overview")
async def get_system_stats(_admin=Depends(require_role("admin"))):
    return {
        "total_customers": len(store.customers),
        "total_workers": len(store.workers),
        "verified_workers": len([worker for worker in store.workers.values() if worker["is_verified"]]),
        "total_tasks": len(store.tasks),
        "completed_tasks": len([task for task in store.tasks.values() if task["status"] == "completed"]),
        "total_payouts": len(store.payouts),
        "total_revenue": round(sum(task["price"] for task in store.tasks.values()), 2),
        "average_rating": round(sum(worker["rating"] for worker in store.workers.values()) / len(store.workers), 2) if store.workers else 0,
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
    return {"stats": await get_system_stats(), "recent_tasks": (await get_detailed_tasks(limit=10)), "verified_workers": [worker for worker in store.list_workers() if worker["is_verified"]]}
