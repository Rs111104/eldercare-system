"""
Dynamic pricing routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.schemas import PricingFactors, PricingResponse
from app.services.pricing_service import PricingService
from supabase import Client

router = APIRouter()

@router.post("/calculate")
async def calculate_pricing(factors: PricingFactors, db: Client = Depends(get_db)):
    """Calculate dynamic pricing based on multiple factors"""
    try:
        service = PricingService(db)
        pricing = await service.calculate_price(
            service_type=factors.service_type.value,
            distance_km=factors.distance_km,
            effort_level=factors.effort_level,
            urgency_level=1,  # Default urgency
            travel_time_minutes=factors.travel_time_minutes
        )
        return pricing
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/calculate-with-urgency")
async def calculate_pricing_with_urgency(
    service_type: str,
    distance_km: float,
    effort_level: int,
    urgency_level: int,
    travel_time_minutes: float = 0.0,
    db: Client = Depends(get_db)
):
    """Calculate pricing with urgency multiplier"""
    try:
        service = PricingService(db)
        pricing = await service.calculate_price(
            service_type=service_type,
            distance_km=distance_km,
            effort_level=effort_level,
            urgency_level=urgency_level,
            travel_time_minutes=travel_time_minutes
        )
        return pricing
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/quick-mode/{service_type}")
async def get_quick_mode_price(
    service_type: str,
    distance_km: float,
    effort_level: int = 2,
    db: Client = Depends(get_db)
):
    """Get price estimate for quick mode"""
    try:
        service = PricingService(db)
        pricing = await service.get_quick_mode_price(service_type, distance_km, effort_level)
        return pricing
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/scheduled-mode/{service_type}")
async def get_scheduled_mode_price(
    service_type: str,
    distance_km: float,
    effort_level: int = 2,
    db: Client = Depends(get_db)
):
    """Get price estimate for scheduled mode"""
    try:
        service = PricingService(db)
        pricing = await service.get_scheduled_mode_price(service_type, distance_km, effort_level)
        return pricing
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/estimate/{task_id}")
async def get_task_price_estimate(task_id: str, db: Client = Depends(get_db)):
    """Get price estimate for a specific task"""
    try:
        response = db.table("tasks").select("*").eq("task_id", task_id).execute()
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task = response.data[0]
        
        return {
            "task_id": task_id,
            "estimated_price": task.get("estimated_price"),
            "actual_price": task.get("actual_price"),
            "pricing_breakdown": {
                "base": 80,
                "distance": 40,
                "effort": 20,
                "urgency": 10
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/worker-earnings/{task_id}")
async def get_worker_earnings(task_id: str, db: Client = Depends(get_db)):
    """Calculate worker earnings from a task"""
    try:
        service = PricingService(db)
        earnings = await service.calculate_worker_earnings(task_id)
        return earnings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/config/{service_type}")
async def update_pricing_config(
    service_type: str,
    base_price: float,
    distance_charge_per_km: float,
    effort_multiplier: float = 1.0,
    db: Client = Depends(get_db)
):
    """Update pricing configuration (admin only)"""
    try:
        service = PricingService(db)
        config = await service.update_pricing_config(
            service_type,
            base_price,
            distance_charge_per_km,
            effort_multiplier
        )
        return config
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
