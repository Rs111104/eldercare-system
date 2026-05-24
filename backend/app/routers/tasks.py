from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models import TaskCreateRequest, TaskStatus, TaskUpdateRequest
from app.store import store
from app.core.cache import cache_response, invalidate_task_cache
from app.core.utils import sanitize_text

router = APIRouter()


@router.post("/create")
async def create_task(payload: TaskCreateRequest):
    customer_id = payload.customer_id or (next(iter(store.customers.keys()), None) or "guest-customer")
    customer = store.get_customer(customer_id)
    if not customer:
        store.customers[customer_id] = {
            "id": customer_id,
            "phone": customer_id,
            "name": "Customer",
            "address": "",
            "lat": payload.location_lat,
            "lng": payload.location_lng,
            "created_at": store._now(),
        }
        customer = store.get_customer(customer_id)

    service_type = payload.service_type or payload.task_type or "other"
    urgency = payload.urgency or (1.0 + (((payload.urgency_level or 1) - 1) * 0.125))
    pricing = store.get_pricing_config(service_type) or store.get_pricing_config("other") or {"base_price": 100.0}
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
    nearest_workers = store.find_nearest_workers(customer.get("lat") or 0.0, customer.get("lng") or 0.0, service_type)
    # invalidate available tasks cache so new task surfaces in listings
    try:
        invalidate_task_cache(task["id"])
    except Exception:
        pass
    return {**task, "task_id": task["id"], "matched_workers": nearest_workers}


@router.post("/create-from-voice")
async def create_task_from_voice(customer_id: str = Form(...), location_lat: float = Form(...), location_lng: float = Form(...), audio_file: UploadFile = File(...)):
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
    return {"task": task, "task_id": task["id"], "transcription": "voice note received", "classification": {"task_type": "help", "urgency_level": 2, "location": {"lat": location_lat, "lng": location_lng}}}


@router.get("/{task_id}")
@cache_response(ttl=30)
async def get_task(task_id: str):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {**task, "task_id": task_id}

@router.put("/{task_id}")
async def update_task(task_id: str, payload: TaskUpdateRequest):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
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
async def cancel_task(task_id: str, reason: str = ""):
    cancelled = store.cancel_task(task_id, reason)
    try:
        invalidate_task_cache(task_id)
    except Exception:
        pass
    return {**cancelled, "task_id": task_id}


@router.get("/customer/{customer_id}")
async def get_customer_tasks(customer_id: str):
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
