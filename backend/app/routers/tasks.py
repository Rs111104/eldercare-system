from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models import ReviewCreateRequest, TaskCreateRequest, TaskStatus, TaskUpdateRequest
from app.store import store
from app.core import metrics
from app.core.deps import get_current_user, require_role
from app.core.cache import cache_response, invalidate_task_cache
from app.core.utils import sanitize_text
from app.services.task_intelligence import TaskIntelligenceService

router = APIRouter()


def _can_access_task(user, task: dict) -> bool:
    role = getattr(user, "user_type", None)
    user_id = getattr(user, "user_id", None)
    return role == "admin" or user_id in {task.get("customer_id"), task.get("worker_id"), task.get("assigned_worker_id")}


def _require_task_access(user, task: dict) -> None:
    if not _can_access_task(user, task):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/create")
async def create_task(payload: TaskCreateRequest, _user=Depends(require_role("customer"))):
    # customer_id is required and must refer to an existing customer owned by the authenticated user
    customer_id = payload.customer_id or getattr(_user, "user_id", None)
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")

    customer = store.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    # ensure authenticated user owns the customer_id
    if getattr(_user, "user_id", None) != customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    service_type = payload.service_type or payload.task_type or "other"
    urgency = payload.urgency or (1.0 + (((payload.urgency_level or 1) - 1) * 0.125))
    pricing = store.get_pricing_config(service_type) or store.get_pricing_config("other") or {"base_price": 100.0}
    estimate = TaskIntelligenceService().estimate(store, customer_id, service_type, 0.0, urgency)
    task = store.create_task(
        customer_id=customer_id,
        service_type=service_type,
        description=sanitize_text(payload.description),
        urgency=urgency,
        base_price=float(pricing.get("base_price", 100.0)),
        distance_km=0.0,
        worker_id=payload.worker_id,
        voice_note_url=payload.voice_note_url,
        title=payload.title,
        same_day_bundle=payload.same_day_bundle,
    )
    task = store.update_task(
        task["id"],
        estimated_duration_minutes=estimate.duration_minutes,
        estimated_price=estimate.estimated_price,
        suggested_recurring_schedule="weekly" if estimate.suggest_weekly else None,
    )
    nearest_workers = store.find_nearest_workers(customer.get("lat") or 0.0, customer.get("lng") or 0.0, service_type)
    # invalidate available tasks cache so new task surfaces in listings
    try:
        invalidate_task_cache(task["id"])
    except Exception:
        pass
    try:
        if metrics.TASKS_CREATED is not None:
            metrics.TASKS_CREATED.labels(service_type=service_type, status=task["status"]).inc()
    except Exception:
        pass
    return {**task, "task_id": task["id"], "matched_workers": nearest_workers}


@router.post("/create-from-voice")
async def create_task_from_voice(customer_id: str = Form(...), location_lat: float = Form(...), location_lng: float = Form(...), audio_file: UploadFile = File(...), _user=Depends(require_role("customer"))):
    if getattr(_user, "user_id", None) != customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not store.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    content = await audio_file.read()
    description = f"Voice note request ({len(content)} bytes)"
    task = store.create_task(
        customer_id=customer_id,
        service_type="help",
        description=description,
        urgency=1.25,
        base_price=150.0,
        distance_km=0.0,
        voice_note_url=audio_file.filename,
    )
    store.store_whatsapp_message(phone=customer_id, direction="in", message_type="audio", content=audio_file.filename, task_id=task["id"])
    try:
        if metrics.TASKS_CREATED is not None:
            metrics.TASKS_CREATED.labels(service_type="help", status=task["status"]).inc()
    except Exception:
        pass
    return {"task": task, "task_id": task["id"], "transcription": "voice note received", "classification": {"task_type": "help", "urgency_level": 2, "location": {"lat": location_lat, "lng": location_lng}}}


@router.get("/{task_id}")
@cache_response(ttl=30)
async def get_task(task_id: str, _user=Depends(get_current_user)):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_task_access(_user, task)
    return {**task, "task_id": task_id}

@router.put("/{task_id}")
async def update_task(task_id: str, payload: TaskUpdateRequest, _user=Depends(get_current_user)):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _require_task_access(_user, task)
    updates = {}
    if payload.status is not None:
        updates["status"] = payload.status.value
    if payload.worker_id is not None:
        updates["worker_id"] = payload.worker_id
    if payload.description is not None:
        updates["description"] = sanitize_text(payload.description)
    if payload.urgency is not None:
        updates["urgency"] = payload.urgency
    updated = store.update_task(task_id, **updates)
    try:
        invalidate_task_cache(task_id)
    except Exception:
        pass
    return {**updated, "task_id": task_id}


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, reason: str = "", _user=Depends(get_current_user)):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if getattr(_user, "user_type", None) != "admin" and getattr(_user, "user_id", None) != task.get("customer_id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    cancelled = store.cancel_task(task_id, reason)
    try:
        invalidate_task_cache(task_id)
    except Exception:
        pass
    return {**cancelled, "task_id": task_id}


@router.post("/{task_id}/review")
async def rate_task(task_id: str, payload: ReviewCreateRequest, _user=Depends(require_role("customer"))):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if getattr(_user, "user_id", None) != task.get("customer_id") or payload.customer_id != task.get("customer_id"):
        raise HTTPException(status_code=403, detail="Forbidden")
    worker_id = task.get("worker_id") or task.get("assigned_worker_id")
    if payload.worker_id != worker_id:
        raise HTTPException(status_code=400, detail="Review worker does not match task")
    try:
        review = store.add_review(task_id, payload.customer_id, payload.worker_id, payload.rating, sanitize_text(payload.comment) or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        invalidate_task_cache(task_id)
    except Exception:
        pass
    return {"review": review, "task": {**store.tasks[task_id], "task_id": task_id}}


@router.get("/customer/{customer_id}")
async def get_customer_tasks(customer_id: str, _user=Depends(get_current_user)):
    if not store.get_customer(customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")
    if getattr(_user, "user_type", None) != "admin" and getattr(_user, "user_id", None) != customer_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return [dict(task, task_id=task["id"]) for task in store.list_tasks(customer_id=customer_id)]


@router.get("/available/quick")
@cache_response(ttl=10)
async def get_available_quick_tasks(service_type: str | None = None):
    tasks = store.list_tasks(status="created")
    if service_type:
        tasks = [task for task in tasks if task["service_type"] == service_type]
    return tasks


@router.get("/available/scheduled")
async def get_available_scheduled_tasks(service_type: str | None = None):
    return await get_available_quick_tasks(service_type)
