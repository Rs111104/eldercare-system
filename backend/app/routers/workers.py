from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.models import TaskStatus, WorkerLocationRequest
from app.store import store
from app.core.cache import cache_response, invalidate_worker_cache, invalidate_task_cache
from app.core.redis_client import get_redis
from app.core.deps import get_current_user, require_role
from app.core.utils import sanitize_text
from app.utils.geo import haversine
import time
import json

router = APIRouter()


def _serialize_worker(worker: dict) -> dict:
    return {
        **worker,
        "worker_id": worker["id"],
        "phone_number": worker["phone"],
        "service_types": [worker.get("service_type")] if worker.get("service_type") else [],
    }


def _serialize_task(task: dict) -> dict:
    return {**task, "task_id": task["id"], "assigned_worker_id": task.get("assigned_worker_id", task.get("worker_id"))}


def _require_worker_or_admin(worker_id: str, user) -> None:
    if getattr(user, "user_type", None) != "admin" and getattr(user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/{worker_id}")
@cache_response(ttl=30)
async def get_worker(worker_id: str):
    worker = store.get_worker(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return _serialize_worker(worker)


@router.post("/onboard")
async def onboard_worker(payload: dict, _user=Depends(require_role("worker"))):
    worker_id = payload.get("worker_id") or getattr(_user, "user_id", None)
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if payload.get("full_name"):
        worker["name"] = sanitize_text(payload["full_name"])
    service_types = payload.get("service_types") or []
    if service_types:
        worker["service_type"] = sanitize_text(service_types[0])
    worker["onboarding"] = {
        "bio": sanitize_text(payload.get("bio", "")),
        "experience_years": float(payload.get("experience_years") or 0),
        "hourly_rate": float(payload.get("hourly_rate") or 0),
        "languages": [sanitize_text(lang) for lang in payload.get("languages", [])],
        "availability": sanitize_text(payload.get("availability", "full_time")),
        "certifications": [sanitize_text(item) for item in payload.get("certifications", [])],
    }
    try:
        invalidate_worker_cache(worker_id)
    except Exception:
        pass
    return {"status": "submitted", "worker": _serialize_worker(store.get_worker(worker_id))}


@router.put("/{worker_id}/location")
async def update_worker_location(worker_id: str, payload: WorkerLocationRequest, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    prev_lat = worker.get("current_lat")
    prev_lng = worker.get("current_lng")
    worker["current_lat"] = payload.lat
    worker["current_lng"] = payload.lng
    # publish to realtime websocket via redis channel if moved >50m and at most every 10s
    try:
        moved = True
        if prev_lat is not None and prev_lng is not None:
            # haversine returns km; convert to meters for >50m check
            dist_m = haversine(prev_lat, prev_lng, payload.lat, payload.lng) * 1000.0
            moved = dist_m >= 50.0

        if moved:
            r = get_redis()
            now_ts = int(time.time())
            if r:
                last_key = f"worker:{worker_id}:last_pub"
                last = r.get(last_key)
                if last and int(last) + 10 > now_ts:
                    # skip publish, throttled
                    pass
                else:
                    r.set(last_key, now_ts)
                    payload_msg = {"worker_id": worker_id, "lat": payload.lat, "lng": payload.lng, "ts": now_ts}
                    try:
                        r.publish("tracking:channel", json.dumps(payload_msg))
                    except Exception:
                        pass
            else:
                # no redis, still no-op publish
                pass
    except Exception:
        pass
    try:
        invalidate_worker_cache(worker_id)
    except Exception:
        pass
    return _serialize_worker(store.get_worker(worker_id))


@router.get("/{worker_id}/available-tasks")
async def get_available_tasks(worker_id: str, service_type: str | None = None, _user=Depends(get_current_user)):
    _require_worker_or_admin(worker_id, _user)
    worker = store.workers.get(worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    service_type = service_type or worker.get("service_type")
    tasks = [_serialize_task(task) for task in store.list_tasks(status="created") if task["service_type"] == service_type]
    return tasks


@router.post("/{worker_id}/accept-task/{task_id}")
async def accept_task(worker_id: str, task_id: str, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not store.get_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker not found")
    try:
        task = store.tasks.get(task_id)
        if not task:
            raise KeyError("Task not found")
        task["worker_id"] = worker_id
        task["assigned_worker_id"] = worker_id
        if task.get("lifecycle_status") == "REQUESTED":
            store.transition_task(task_id, "MATCHED", worker_id, "worker", "worker_match")
            task = store.transition_task(task_id, "CONFIRMED", worker_id, "worker", "worker_accept")
        else:
            task = store.update_task(task_id, worker_id=worker_id, status=TaskStatus.assigned.value)
        try:
            invalidate_task_cache(task_id)
            invalidate_worker_cache(worker_id)
        except Exception:
            pass
        return _serialize_task(task)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{worker_id}/reject-task/{task_id}")
async def reject_task(worker_id: str, task_id: str, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not store.get_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker not found")
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "task_id": task_id, "worker_id": worker_id}


@router.post("/{worker_id}/check-in/{task_id}")
async def check_in(worker_id: str, task_id: str, payload: dict | None = None, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    payload = payload or {}
    lat = float(payload.get("latitude", payload.get("lat", 0.0)))
    lng = float(payload.get("longitude", payload.get("lng", 0.0)))
    event = store.record_tracking(task_id, worker_id, lat, lng, event_type="check_in")
    task = store.tasks.get(task_id)
    if task and task.get("lifecycle_status") == "CONFIRMED":
        store.transition_task(task_id, "IN_PROGRESS", worker_id, "worker", "worker_check_in")
    else:
        store.update_task(task_id, status=TaskStatus.in_progress.value, lifecycle_status="IN_PROGRESS")
    return event


@router.post("/{worker_id}/check-out/{task_id}")
async def check_out(worker_id: str, task_id: str, payload: dict | None = None, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    payload = payload or {}
    lat = float(payload.get("latitude", payload.get("lat", 0.0)))
    lng = float(payload.get("longitude", payload.get("lng", 0.0)))
    report = payload.get("report", "Completed")
    proof_photos = payload.get("proof_photos") or ([] if payload.get("proof_photo_url") is None else [payload.get("proof_photo_url")])
    event = store.record_tracking(task_id, worker_id, lat, lng, event_type="check_out")
    task = store.complete_task(task_id)
    store.record_payout_split(worker_id, task_id, float(task.get("price", 0)))
    return {**event, "report": report, "proof_photos": proof_photos or [], "task_status": task["status"]}


@router.get("/{worker_id}/stats")
async def get_worker_stats(worker_id: str, _user=Depends(get_current_user)):
    _require_worker_or_admin(worker_id, _user)
    if not store.get_worker(worker_id):
        raise HTTPException(status_code=404, detail="Worker not found")
    tasks = store.list_tasks(worker_id=worker_id)
    completed = [task for task in tasks if task["status"] == "completed"]
    earnings = store.get_earnings_for_worker(worker_id)
    return {"total_tasks": len(tasks), "tasks_completed": len(completed), "completed_tasks": len(completed), "earnings": earnings, "rating": store.get_worker(worker_id)["rating"]}


@router.get("/available/by-service/{service_type}")
async def get_available_workers_by_service(service_type: str):
    return [_serialize_worker(worker) for worker in store.list_workers() if worker["service_type"] == service_type and worker["is_verified"]]
