"""
Payout management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.schemas import PayoutStatus
from app.services.payout_service import PayoutService
from app.services.notification_service import NotificationService
from supabase import Client
from datetime import datetime

router = APIRouter()

@router.get("/worker/{worker_id}")
async def get_worker_payouts(worker_id: str, db: Client = Depends(get_db)):
    """Get all payouts for a worker"""
    try:
        service = PayoutService(db)
        payouts = await service.get_pending_payouts(worker_id)
        return payouts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/worker/{worker_id}/earnings")
async def get_worker_earnings(worker_id: str, db: Client = Depends(get_db)):
    """Get worker's total earnings"""
    try:
        service = PayoutService(db)
        earnings = await service.get_worker_total_earnings(worker_id)
        return earnings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/worker/{worker_id}/history")
async def get_payout_history(
    worker_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Client = Depends(get_db)
):
    """Get payout history for a worker"""
    try:
        service = PayoutService(db)
        history = await service.get_payout_history(worker_id, limit, offset)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/process/{task_id}")
async def process_task_payout(task_id: str, db: Client = Depends(get_db)):
    """Process payout for completed task"""
    try:
        # Get task details
        task_response = db.table("tasks").select("*").eq("task_id", task_id).execute()
        
        if not task_response.data or task_response.data[0].get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task not completed"
            )
        
        task = task_response.data[0]
        worker_id = task.get("assigned_worker_id")
        total_amount = task.get("actual_price", task.get("estimated_price", 0))
        
        # Create payout record
        service = PayoutService(db)
        payout = await service.process_task_payout(task_id, worker_id, total_amount)
        
        # Send notifications
        worker_response = db.table("workers").select("phone_number").eq("worker_id", worker_id).execute()
        if worker_response.data:
            notification = NotificationService()
            immediate_amount = total_amount * 0.75
            await notification.notify_payout_processed(
                worker_phone=worker_response.data[0]["phone_number"],
                amount=immediate_amount,
                payout_type="immediate"
            )
        
        return payout
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{payout_id}/release-immediate")
async def release_immediate_payout(payout_id: str, db: Client = Depends(get_db)):
    """Release immediate 75% payout to worker"""
    try:
        service = PayoutService(db)
        success = await service.release_immediate_payout(payout_id)
        
        if success:
            return {"status": "released"}
        else:
            raise Exception("Failed to release payout")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{payout_id}/release-verification")
async def release_verification_payout(payout_id: str, db: Client = Depends(get_db)):
    """Release 25% verification payout after fraud checks"""
    try:
        service = PayoutService(db)
        success = await service.release_verification_payout(payout_id)
        
        if success:
            return {"status": "released"}
        else:
            raise Exception("Failed to release payout")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{payout_id}")
async def get_payout_status(payout_id: str, db: Client = Depends(get_db)):
    """Get payout status"""
    try:
        service = PayoutService(db)
        payout = await service.get_payout_status(payout_id)
        return payout
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/pending")
async def get_pending_payouts_stats(db: Client = Depends(get_db)):
    """Get statistics about pending payouts"""
    try:
        response = db.table("payouts").select("total_amount", count="exact").eq("status", "pending").execute()
        
        total_pending = 0
        if response.data:
            total_pending = sum(p.get("total_amount", 0) for p in response.data)
        
        return {
            "count": response.count or 0,
            "total_amount": round(total_pending, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
