"""
Real-time tracking routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket
from app.core.database import get_db
from supabase import Client

router = APIRouter()

@router.post("/{task_id}/check-in")
async def task_check_in(
    task_id: str,
    worker_id: str,
    lat: float,
    lng: float,
    db: Client = Depends(get_db)
):
    """Worker checks in for task"""
    try:
        response = db.table("tracking").insert({
            "task_id": task_id,
            "worker_id": worker_id,
            "event_type": "check_in",
            "latitude": lat,
            "longitude": lng
        }).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{task_id}/check-out")
async def task_check_out(
    task_id: str,
    worker_id: str,
    lat: float,
    lng: float,
    report: str,
    db: Client = Depends(get_db)
):
    """Worker checks out from task"""
    try:
        response = db.table("tracking").insert({
            "task_id": task_id,
            "worker_id": worker_id,
            "event_type": "check_out",
            "latitude": lat,
            "longitude": lng,
            "report": report
        }).execute()
        
        # Update task status to completed
        task_update = db.table("tasks").update({
            "status": "completed"
        }).eq("task_id", task_id).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{task_id}/location")
async def get_task_worker_location(task_id: str, db: Client = Depends(get_db)):
    """Get worker's current location for a task"""
    try:
        response = db.table("tasks").select("assigned_worker_id").eq("task_id", task_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        worker_id = response.data[0].get("assigned_worker_id")
        
        # Get latest location from tracking
        location_response = db.table("tracking").select("latitude, longitude, created_at").eq("task_id", task_id).order("created_at", desc=True).limit(1).execute()
        
        if location_response.data:
            return location_response.data[0]
        
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket for real-time tracking updates"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # TODO: Broadcast to relevant clients
            await websocket.send_json({
                "task_id": task_id,
                "message": data
            })
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()
