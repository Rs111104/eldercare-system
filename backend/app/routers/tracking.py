from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app.core.deps import get_current_user, require_role
from app.store import store

router = APIRouter()


@router.post("/{task_id}/check-in")
async def task_check_in(task_id: str, worker_id: str, lat: float, lng: float, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if worker_id not in {task.get("worker_id"), task.get("assigned_worker_id")}:
        raise HTTPException(status_code=403, detail="Worker is not assigned to this task")
    return store.record_tracking(task_id, worker_id, lat, lng, event_type="check_in")


@router.post("/{task_id}/check-out")
async def task_check_out(task_id: str, worker_id: str, lat: float, lng: float, report: str, _user=Depends(require_role("worker"))):
    if getattr(_user, "user_id", None) != worker_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if worker_id not in {task.get("worker_id"), task.get("assigned_worker_id")}:
        raise HTTPException(status_code=403, detail="Worker is not assigned to this task")
    event = store.record_tracking(task_id, worker_id, lat, lng, event_type="check_out")
    store.complete_task(task_id)
    return {**event, "report": report}


@router.get("/{task_id}/location")
async def get_task_worker_location(task_id: str, _user=Depends(get_current_user)):
    task = store.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    user_id = getattr(_user, "user_id", None)
    if getattr(_user, "user_type", None) != "admin" and user_id not in {task.get("customer_id"), task.get("worker_id"), task.get("assigned_worker_id")}:
        raise HTTPException(status_code=403, detail="Forbidden")
    location = store.get_latest_location(task_id)
    if not location:
        return None
    return location


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        await websocket.send_json({"task_id": task_id, "status": "connected"})
        while True:
            message = await websocket.receive_text()
            await websocket.send_json({"task_id": task_id, "message": message})
    except WebSocketDisconnect:
        return
