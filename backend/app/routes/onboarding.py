"""
Worker onboarding routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from app.core.database import get_db
from app.services.onboarding_service import OnboardingService
from supabase import Client

router = APIRouter()

@router.post("/{worker_id}/submit-document")
async def submit_verification_document(
    worker_id: str,
    document_type: str,
    document_file: UploadFile = File(...),
    db: Client = Depends(get_db)
):
    """Submit verification document (ID, license, background check)"""
    try:
        # Read file
        content = await document_file.read()
        
        # TODO: Upload to cloud storage (S3, GCS, or Supabase Storage)
        # document_url = upload_to_storage(content, worker_id, document_type)
        document_url = f"https://storage.example.com/{worker_id}/{document_type}/{document_file.filename}"
        
        service = OnboardingService(db)
        worker = await service.submit_verification(worker_id, document_type, document_url)
        
        return {
            "status": "submitted",
            "document_type": document_type,
            "worker": worker
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{worker_id}/verification-status")
async def get_verification_status(worker_id: str, db: Client = Depends(get_db)):
    """Get worker's verification status"""
    try:
        service = OnboardingService(db)
        worker = await service.get_verification_details(worker_id)
        
        return {
            "worker_id": worker_id,
            "is_verified": worker.get("is_verified"),
            "documents": worker.get("documents_verified", {}),
            "created_at": worker.get("created_at")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/approve")
async def approve_worker(worker_id: str, notes: str = "", db: Client = Depends(get_db)):
    """Approve worker (admin only)"""
    try:
        service = OnboardingService(db)
        worker = await service.approve_worker(worker_id, notes)
        
        return {
            "status": "approved",
            "worker": worker
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{worker_id}/reject")
async def reject_worker(worker_id: str, reason: str, db: Client = Depends(get_db)):
    """Reject worker application (admin only)"""
    try:
        service = OnboardingService(db)
        success = await service.reject_worker(worker_id, reason)
        
        return {
            "status": "rejected",
            "success": success
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/pending-verifications")
async def get_pending_verifications(limit: int = 10, db: Client = Depends(get_db)):
    """Get workers awaiting verification (admin only)"""
    try:
        service = OnboardingService(db)
        workers = await service.get_pending_verifications(limit)
        
        return {
            "count": len(workers),
            "workers": workers
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{worker_id}/profile")
async def update_worker_profile(
    worker_id: str,
    name: str = None,
    email: str = None,
    service_types: list = None,
    db: Client = Depends(get_db)
):
    """Update worker profile during onboarding"""
    try:
        service = OnboardingService(db)
        worker = await service.update_worker_profile(
            worker_id,
            name=name,
            email=email,
            service_types=service_types
        )
        
        return worker
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
