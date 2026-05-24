"""
Tasks management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from app.core.database import get_db
from app.schemas import TaskCreate, TaskResponse, TaskUpdate, TaskStatus
from app.services.task_service import TaskService
from app.services.voice_service import VoiceProcessingService
from app.services.notification_service import NotificationService
from supabase import Client
from datetime import datetime
from typing import Optional

router = APIRouter()

@router.post("/create")
async def create_task(task: TaskCreate, db: Client = Depends(get_db)):
    """Create a new task from customer request"""
    try:
        service = TaskService(db)
        
        result = await service.create_task_from_voice(
            customer_id=task.customer_id,
            title=task.title,
            description=task.description,
            task_type=task.task_type.value,
            location_lat=task.location_lat,
            location_lng=task.location_lng,
            urgency_level=task.urgency_level
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/create-from-voice")
async def create_task_from_voice(
    customer_id: str = Form(...),
    location_lat: float = Form(...),
    location_lng: float = Form(...),
    audio_file: UploadFile = File(...),
    db: Client = Depends(get_db)
):
    """Create task from WhatsApp voice note"""
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        # Transcribe audio
        voice_service = VoiceProcessingService()
        transcribed_text = await voice_service.transcribe_audio(audio_content)
        
        if not transcribed_text:
            raise Exception("Failed to transcribe audio")
        
        # Classify voice request
        classification = await voice_service.classify_voice_request(transcribed_text)
        
        # Create task
        task_service = TaskService(db)
        task = await task_service.create_task_from_voice(
            customer_id=customer_id,
            title=classification.get("title", "Service Request"),
            description=classification.get("description", transcribed_text),
            task_type=classification.get("task_type", "other"),
            location_lat=location_lat,
            location_lng=location_lng,
            voice_note_url=None,  # Store audio file URL if needed
            urgency_level=classification.get("urgency_level", 2)
        )
        
        # Get customer info for notification
        customer = db.table("customers").select("phone_number").eq("user_id", customer_id).execute()
        if customer.data:
            notification = NotificationService()
            await notification.notify_task_created(
                customer_phone=customer.data[0]["phone_number"],
                customer_name=customer.data[0].get("name", "Customer"),
                task_title=task.get("title"),
                estimated_price=task.get("estimated_price")
            )
        
        return {
            "task": task,
            "transcription": transcribed_text,
            "classification": classification
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{task_id}")
async def get_task(task_id: str, db: Client = Depends(get_db)):
    """Get task details"""
    try:
        service = TaskService(db)
        task = await service.get_task_details(task_id)
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{task_id}")
async def update_task(task_id: str, update: TaskUpdate, db: Client = Depends(get_db)):
    """Update task status"""
    try:
        service = TaskService(db)
        if update.status:
            task = await service.update_task_status(task_id, update.status)
        elif update.assigned_worker_id:
            task = await service.assign_worker_to_task(task_id, update.assigned_worker_id)
        else:
            raise Exception("No updates provided")
        
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, reason: str = "", db: Client = Depends(get_db)):
    """Cancel a task"""
    try:
        service = TaskService(db)
        task = await service.cancel_task(task_id, reason)
        return task
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/customer/{customer_id}")
async def get_customer_tasks(customer_id: str, db: Client = Depends(get_db)):
    """Get all tasks for a customer"""
    try:
        response = db.table("tasks").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/available/quick")
async def get_available_quick_tasks(service_type: Optional[str] = None, db: Client = Depends(get_db)):
    """Get all available quick mode tasks"""
    try:
        query = db.table("tasks").select("*").eq("mode", "quick").eq("status", "created")
        
        if service_type:
            response = query.contains("preferred_service_types", [service_type]).execute()
        else:
            response = query.execute()
        
        return response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/active")
async def get_active_tasks_count(db: Client = Depends(get_db)):
    """Get count of active tasks"""
    try:
        response = db.table("tasks").select("task_id", count="exact").in_("status", ["created", "assigned", "accepted", "in_progress"]).execute()
        return {
            "active_tasks": response.count or 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
