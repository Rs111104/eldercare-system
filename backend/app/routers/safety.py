from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import require_role
from app.store import store

router = APIRouter()


@router.post("/customers/{customer_id}/trusted-contacts")
async def set_trusted_contacts(customer_id: str, contacts: list[dict], _user=Depends(require_role("customer"))):
    if customer_id not in store.customers:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, "trusted_contacts": store.set_trusted_contacts(customer_id, contacts)}


@router.post("/tasks/{task_id}/arrival-confirmation")
async def confirm_arrival(task_id: str, worker_id: str, _user=Depends(require_role("worker"))):
    try:
        return store.confirm_arrival(task_id, worker_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/tasks/{task_id}/sos")
async def send_sos(task_id: str, customer_id: str, _user=Depends(require_role("customer"))):
    try:
        return store.send_sos_alert(task_id, customer_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workers/{worker_id}/panic-report")
async def panic_report(worker_id: str, reason: str, _user=Depends(require_role("admin"))):
    try:
        return store.freeze_worker(worker_id, reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/workers/{worker_id}/badge-tier")
async def get_badge_tier(worker_id: str, _user=Depends(require_role("worker"))):
    if worker_id not in store.workers:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"worker_id": worker_id, "badge_tier": store.get_worker_badge_tier(worker_id)}
