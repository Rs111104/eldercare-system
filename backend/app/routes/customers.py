"""
Customer routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from supabase import Client

router = APIRouter()

@router.get("/{customer_id}")
async def get_customer(customer_id: str, db: Client = Depends(get_db)):
    """Get customer details"""
    try:
        response = db.table("customers").select("*").eq("user_id", customer_id).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{customer_id}/tasks")
async def get_customer_tasks(customer_id: str, db: Client = Depends(get_db)):
    """Get customer's task history"""
    try:
        response = db.table("tasks").select("*").eq("customer_id", customer_id).order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{customer_id}/active-task")
async def get_customer_active_task(customer_id: str, db: Client = Depends(get_db)):
    """Get customer's currently active task"""
    try:
        response = db.table("tasks").select("*").eq("customer_id", customer_id).in_("status", ["assigned", "accepted", "in_progress"]).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
