"""
Workers management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.services.worker_service import WorkerService
from supabase import Client

router = APIRouter()

@router.get("/{worker_id}")
async def get_worker(worker_id: str, db: Client = Depends(get_db)):
    """Get worker details"""
    try:
        response = db.table("workers").select("*").eq("worker_id", worker_id).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{worker_id}/location")
async def update_worker_location(worker_id: str, lat: float, lng: float, db: Client = Depends(get_db)):
    """Update worker's current location"""
    try:
        service = WorkerService(db)
        worker = await service.update_location(worker_id, lat, lng)
        return worker
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{worker_id}/available-tasks")
async def get_available_tasks(worker_id: str, service_type: str = None, db: Client = Depends(get_db)):
    """Get available tasks for worker"""
    try:
        service = WorkerService(db)
        tasks = await service.get_available_tasks(worker_id, service_type)
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/accept-task/{task_id}")
async def worker_accept_task(worker_id: str, task_id: str, db: Client = Depends(get_db)):
    """Worker accepts a task"""
    try:
        service = WorkerService(db)
        task = await service.accept_task(worker_id, task_id)
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/reject-task/{task_id}")
async def worker_reject_task(worker_id: str, task_id: str, db: Client = Depends(get_db)):
    """Worker rejects a task"""
    try:
        service = WorkerService(db)
        result = await service.reject_task(worker_id, task_id)
        return {"success": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/check-in/{task_id}")
async def worker_check_in(worker_id: str, task_id: str, lat: float, lng: float, db: Client = Depends(get_db)):
    """Worker checks in at task location"""
    try:
        service = WorkerService(db)
        tracking = await service.check_in(worker_id, task_id, lat, lng)
        return tracking
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/check-out/{task_id}")
async def worker_check_out(
    worker_id: str,
    task_id: str,
    lat: float,
    lng: float,
    report: str,
    proof_photos: list = None,
    db: Client = Depends(get_db)
):
    """Worker checks out and completes task"""
    try:
        service = WorkerService(db)
        tracking = await service.check_out(worker_id, task_id, lat, lng, report, proof_photos)
        return tracking
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{worker_id}/stats")
async def get_worker_stats(worker_id: str, db: Client = Depends(get_db)):
    """Get worker performance statistics"""
    try:
        service = WorkerService(db)
        stats = await service.get_worker_stats(worker_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/available/by-service/{service_type}")
async def get_available_workers_by_service(service_type: str, db: Client = Depends(get_db)):
    """Get available workers for specific service type"""
    try:
        response = db.table("workers").select("*").contains("service_types", [service_type]).eq("is_verified", True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
