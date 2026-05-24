from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.store import store

router = APIRouter()


@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    customer = store.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/tasks")
async def get_customer_tasks(customer_id: str):
    return [dict(task, task_id=task["id"]) for task in store.list_tasks(customer_id=customer_id)]


@router.get("/{customer_id}/active-task")
async def get_customer_active_task(customer_id: str):
    tasks = [task for task in store.list_tasks(customer_id=customer_id) if task["status"] in {"assigned", "accepted", "in_progress"}]
    return (dict(tasks[0], task_id=tasks[0]["id"]) if tasks else None)
