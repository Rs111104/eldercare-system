"""
Admin routes for system management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from supabase import Client
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/stats/overview")
async def get_system_stats(db: Client = Depends(get_db)):
    """Get overall system statistics"""
    try:
        # Get counts
        customers = db.table("customers").select("user_id", count="exact").execute()
        workers = db.table("workers").select("worker_id", count="exact").execute()
        tasks = db.table("tasks").select("task_id", count="exact").execute()
        payouts = db.table("payouts").select("payout_id", count="exact").execute()
        
        # Get completed tasks
        completed = db.table("tasks").select("task_id", count="exact").eq("status", "completed").execute()
        
        # Get revenue
        payouts_data = db.table("payouts").select("total_amount").execute()
        total_revenue = sum(p.get("total_amount", 0) for p in (payouts_data.data or []))
        
        return {
            "total_customers": customers.count or 0,
            "total_workers": workers.count or 0,
            "verified_workers": 0,  # TODO: count verified
            "total_tasks": tasks.count or 0,
            "completed_tasks": completed.count or 0,
            "total_payouts": payouts.count or 0,
            "total_revenue": round(total_revenue, 2),
            "average_rating": 4.8  # TODO: calculate from reviews
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/tasks")
async def get_task_statistics(days: int = 7, db: Client = Depends(get_db)):
    """Get task statistics for period"""
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        response = db.table("tasks").select("status").gte("created_at", start_date).execute()
        
        if not response.data:
            return {
                "period_days": days,
                "created": 0,
                "assigned": 0,
                "in_progress": 0,
                "completed": 0,
                "cancelled": 0
            }
        
        stats = {
            "period_days": days,
            "created": sum(1 for t in response.data if t["status"] == "created"),
            "assigned": sum(1 for t in response.data if t["status"] == "assigned"),
            "accepted": sum(1 for t in response.data if t["status"] == "accepted"),
            "in_progress": sum(1 for t in response.data if t["status"] == "in_progress"),
            "completed": sum(1 for t in response.data if t["status"] == "completed"),
            "cancelled": sum(1 for t in response.data if t["status"] == "cancelled")
        }
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/workers")
async def get_worker_statistics(db: Client = Depends(get_db)):
    """Get worker performance statistics"""
    try:
        workers = db.table("workers").select("*").execute()
        
        total_workers = len(workers.data) if workers.data else 0
        verified = sum(1 for w in (workers.data or []) if w.get("is_verified"))
        
        return {
            "total_workers": total_workers,
            "verified_workers": verified,
            "pending_verification": total_workers - verified,
            "total_tasks_completed": 0,  # TODO: sum from tasks
            "average_rating": 4.8  # TODO: calculate
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/stats/revenue")
async def get_revenue_statistics(days: int = 30, db: Client = Depends(get_db)):
    """Get revenue statistics"""
    try:
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        payouts = db.table("payouts").select("*").gte("created_at", start_date).execute()
        
        if not payouts.data:
            return {
                "period_days": days,
                "total_revenue": 0,
                "immediate_payouts": 0,
                "pending_verification": 0,
                "completed_payouts": 0
            }
        
        total = sum(p.get("total_amount", 0) for p in payouts.data)
        immediate = sum(p.get("immediate_payout", 0) for p in payouts.data if p["status"] in ["pending", "processed"])
        pending = sum(p.get("verification_payout", 0) for p in payouts.data if p["status"] == "pending")
        completed = sum(p.get("verification_payout", 0) for p in payouts.data if p["status"] == "processed")
        
        return {
            "period_days": days,
            "total_revenue": round(total, 2),
            "immediate_payouts": round(immediate, 2),
            "pending_verification": round(pending, 2),
            "completed_payouts": round(completed, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tasks/detailed")
async def get_detailed_tasks(status: str = None, limit: int = 50, db: Client = Depends(get_db)):
    """Get detailed task information"""
    try:
        if status:
            response = db.table("tasks").select("*").eq("status", status).order("created_at", desc=True).limit(limit).execute()
        else:
            response = db.table("tasks").select("*").order("created_at", desc=True).limit(limit).execute()
        
        return response.data or []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/pricing-config/{service_type}")
async def update_pricing_config(
    service_type: str,
    base_price: float,
    distance_charge: float,
    effort_multiplier: float = 1.0,
    db: Client = Depends(get_db)
):
    """Update pricing configuration (admin)"""
    try:
        response = db.table("pricing_config").upsert({
            "service_type": service_type,
            "base_price": base_price,
            "distance_charge_per_km": distance_charge,
            "effort_multiplier": effort_multiplier
        }).execute()
        
        return response.data[0] if response.data else None
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/dashboard")
async def get_admin_dashboard(db: Client = Depends(get_db)):
    """Get comprehensive admin dashboard data"""
    try:
        stats = {
            "overview": {
                "customers": "...",
                "workers": "...",
                "active_tasks": "...",
                "daily_revenue": "..."
            },
            "tasks": {
                "created": 0,
                "in_progress": 0,
                "completed": 0
            },
            "payouts": {
                "pending": 0,
                "processed": 0
            }
        }
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
