from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.store import store

router = APIRouter()


@router.post("/{task_id}/check-in")
async def task_check_in(task_id: str, worker_id: str, lat: float, lng: float):
    return store.record_tracking(task_id, worker_id, lat, lng, event_type="check_in")


@router.post("/{task_id}/check-out")
async def task_check_out(task_id: str, worker_id: str, lat: float, lng: float, report: str):
    event = store.record_tracking(task_id, worker_id, lat, lng, event_type="check_out")
    store.complete_task(task_id)
    return {**event, "report": report}


@router.get("/{task_id}/location")
async def get_task_worker_location(task_id: str):
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
