from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.store import store

router = APIRouter()


def _require_customer_access(customer_id: str, user) -> None:
    if getattr(user, "user_type", None) != "admin" and getattr(user, "user_id", None) != customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/{customer_id}")
async def get_customer(customer_id: str, _user=Depends(get_current_user)):
    customer = store.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    _require_customer_access(customer_id, _user)
    return customer


@router.get("/{customer_id}/tasks")
async def get_customer_tasks(customer_id: str, _user=Depends(get_current_user)):
    if not store.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    _require_customer_access(customer_id, _user)
    return [dict(task, task_id=task["id"]) for task in store.list_tasks(customer_id=customer_id)]


@router.get("/{customer_id}/active-task")
async def get_customer_active_task(customer_id: str, _user=Depends(get_current_user)):
    if not store.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    _require_customer_access(customer_id, _user)
    tasks = [task for task in store.list_tasks(customer_id=customer_id) if task["status"] in {"assigned", "accepted", "in_progress"}]
    return (dict(tasks[0], task_id=tasks[0]["id"]) if tasks else None)
