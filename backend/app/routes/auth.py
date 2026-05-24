"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import create_access_token, verify_password, hash_password
from app.core.database import get_db
from app.schemas import UserType, CustomerCreate, WorkerCreate, CustomerResponse, WorkerResponse
from supabase import Client

router = APIRouter()

@router.post("/register/customer")
async def register_customer(user: CustomerCreate, db: Client = Depends(get_db)):
    """Register a new customer"""
    try:
        response = db.table("customers").insert({
            "phone_number": user.phone_number,
            "name": user.name,
            "email": user.email,
            "profile_picture_url": user.profile_picture_url
        }).execute()
        
        if response.data:
            customer = response.data[0]
            token = create_access_token(
                user_id=customer["user_id"],
                phone_number=customer["phone_number"],
                user_type="customer"
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": customer
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/register/worker")
async def register_worker(user: WorkerCreate, db: Client = Depends(get_db)):
    """Register a new worker"""
    try:
        response = db.table("workers").insert({
            "phone_number": user.phone_number,
            "name": user.name,
            "email": user.email,
            "profile_picture_url": user.profile_picture_url,
            "service_types": user.service_types,
            "location_lat": user.location_lat,
            "location_lng": user.location_lng,
            "is_verified": False
        }).execute()
        
        if response.data:
            worker = response.data[0]
            token = create_access_token(
                user_id=worker["worker_id"],
                phone_number=worker["phone_number"],
                user_type="worker"
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": worker
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login")
async def login(phone_number: str, db: Client = Depends(get_db)):
    """Login with phone number (OTP verification would happen here)"""
    try:
        # Check if customer exists
        customer_response = db.table("customers").select("*").eq("phone_number", phone_number).execute()
        
        if customer_response.data:
            customer = customer_response.data[0]
            token = create_access_token(
                user_id=customer["user_id"],
                phone_number=customer["phone_number"],
                user_type="customer"
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_type": "customer"
            }
        
        # Check if worker exists
        worker_response = db.table("workers").select("*").eq("phone_number", phone_number).execute()
        
        if worker_response.data:
            worker = worker_response.data[0]
            token = create_access_token(
                user_id=worker["worker_id"],
                phone_number=worker["phone_number"],
                user_type="worker"
            )
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_type": "worker"
            }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
