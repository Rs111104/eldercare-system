"""
Worker onboarding service - manage worker verification and approval
"""
from datetime import datetime
from app.core.database import get_db
from supabase import Client
from typing import Dict, Any, List, Optional

class OnboardingService:
    def __init__(self, db: Client):
        self.db = db

    async def submit_verification(
        self,
        worker_id: str,
        document_type: str,  # "id", "license", "background_check"
        document_url: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit verification document for worker"""
        
        worker_response = self.db.table("workers").select("documents_verified").eq("worker_id", worker_id).execute()
        
        if not worker_response.data:
            raise Exception("Worker not found")
        
        worker = worker_response.data[0]
        documents_verified = worker.get("documents_verified", {})
        
        # Add new document
        documents_verified[document_type] = {
            "url": document_url,
            "submitted_at": datetime.utcnow().isoformat(),
            "status": "pending",
            "additional_info": additional_info
        }
        
        # Update worker record
        response = self.db.table("workers").update({
            "documents_verified": documents_verified
        }).eq("worker_id", worker_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to submit verification")

    async def approve_worker(
        self,
        worker_id: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Approve worker for platform (admin only)"""
        
        response = self.db.table("workers").update({
            "is_verified": True,
            "rating": 5.0
        }).eq("worker_id", worker_id).execute()
        
        if response.data:
            # Send approval notification
            worker = response.data[0]
            # TODO: Send WhatsApp notification about approval
            return response.data[0]
        
        raise Exception("Failed to approve worker")

    async def reject_worker(
        self,
        worker_id: str,
        reason: str
    ) -> bool:
        """Reject worker application"""
        
        response = self.db.table("workers").update({
            "is_verified": False
        }).eq("worker_id", worker_id).execute()
        
        # TODO: Send rejection notification with reason
        return bool(response.data)

    async def get_pending_verifications(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of workers awaiting verification (admin)"""
        
        response = self.db.table("workers").select("*").eq("is_verified", False).order("created_at").limit(limit).execute()
        
        return response.data or []

    async def get_verification_details(self, worker_id: str) -> Dict[str, Any]:
        """Get worker details for verification review"""
        
        response = self.db.table("workers").select("*").eq("worker_id", worker_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Worker not found")

    async def update_worker_profile(
        self,
        worker_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        profile_picture_url: Optional[str] = None,
        service_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Update worker profile information"""
        
        update_data = {}
        
        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email
        if profile_picture_url:
            update_data["profile_picture_url"] = profile_picture_url
        if service_types:
            update_data["service_types"] = service_types
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        response = self.db.table("workers").update(update_data).eq("worker_id", worker_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to update profile")
