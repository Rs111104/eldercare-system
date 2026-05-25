from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.store import store
from app.core.deps import get_current_user, require_role
from app.core import metrics

router = APIRouter()


def _require_worker_or_admin(worker_id: str, user) -> None:
    if getattr(user, "user_type", None) != "admin" and getattr(user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/worker/{worker_id}")
async def get_worker_payouts(worker_id: str, _user=Depends(get_current_user)):
    _require_worker_or_admin(worker_id, _user)
    return store.get_payouts_for_worker(worker_id)


@router.get("/worker/{worker_id}/earnings")
async def get_worker_earnings(worker_id: str, _user=Depends(get_current_user)):
    _require_worker_or_admin(worker_id, _user)
    return store.get_earnings_for_worker(worker_id)


@router.get("/worker/{worker_id}/history")
async def get_payout_history(worker_id: str, limit: int = 20, offset: int = 0, _user=Depends(get_current_user)):
    _require_worker_or_admin(worker_id, _user)
    payouts = store.get_payouts_for_worker(worker_id)
    return payouts[offset : offset + limit]


@router.post("/process/{task_id}")
async def process_task_payout(task_id: str, _admin=Depends(require_role("admin"))):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    worker_id = task.get("worker_id")
    if not worker_id:
        raise HTTPException(status_code=400, detail="Task has no assigned worker")
    payouts = store.record_payout_split(worker_id, task_id, float(task.get("price", 0)))
    try:
        if metrics.PAYOUTS_PROCESSED is not None:
            metrics.PAYOUTS_PROCESSED.labels(status="created").inc()
    except Exception:
        pass
    return payouts


@router.post("/{payout_id}/release-immediate")
async def release_immediate_payout(payout_id: str, _admin=Depends(require_role("admin"))):
    payout = store.payouts.get(payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    payout["status"] = "released"
    return {"status": "released", "payout_id": payout_id}


@router.post("/{payout_id}/release-verification")
async def release_verification_payout(payout_id: str, _admin=Depends(require_role("admin"))):
    payout = store.payouts.get(payout_id)
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.get("split_type") != "verification":
        raise HTTPException(status_code=400, detail="Payout is not a verification split")
    if payout.get("status") == "released":
        return {"status": "released", "payout_id": payout_id}

    available_at = payout.get("verification_available_at")
    if not available_at:
        created_at = payout.get("created_at")
        if not created_at:
            raise HTTPException(status_code=400, detail="Payout timing metadata missing")
        available_at = (datetime.fromisoformat(created_at) + timedelta(hours=48)).isoformat()
        payout["verification_available_at"] = available_at

    if datetime.fromisoformat(available_at) > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification payout becomes available after 48 hours")

    payout["status"] = "released"
    payout["released_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "released", "payout_id": payout_id}
