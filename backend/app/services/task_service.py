"""
Task service - core business logic for task management
"""
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas import TaskCreate, TaskStatus, PricingFactors
from supabase import Client
from typing import List, Optional, Dict, Any
import json
from app.utils.geo import haversine

class TaskService:
    def __init__(self, db: Client):
        self.db = db

    async def create_task_from_voice(
        self,
        customer_id: str,
        title: str,
        description: str,
        task_type: str,
        location_lat: float,
        location_lng: float,
        voice_note_url: Optional[str] = None,
        urgency_level: int = 1
    ) -> Dict[str, Any]:
        """Create task from voice note"""
        
        # Calculate estimated price based on task type and location
        estimated_price = await self._calculate_estimated_price(
            task_type,
            location_lat,
            location_lng,
            urgency_level
        )
        
        task_data = {
            "customer_id": customer_id,
            "title": title,
            "description": description,
            "task_type": task_type,
            "mode": "quick",  # Default to quick
            "urgency_level": urgency_level,
            "location_lat": location_lat,
            "location_lng": location_lng,
            "status": TaskStatus.CREATED.value,
            "estimated_price": estimated_price,
            "voice_note_url": voice_note_url,
            "preferred_service_types": [task_type]
        }
        
        response = self.db.table("tasks").insert(task_data).execute()
        
        if response.data:
            task = response.data[0]
            # Trigger matching with suitable workers
            await self._match_workers(task["task_id"], task_type, location_lat, location_lng)
            return task
        
        raise Exception("Failed to create task")

    async def _calculate_estimated_price(
        self,
        service_type: str,
        lat: float,
        lng: float,
        urgency_level: int
    ) -> float:
        """Calculate estimated price for task"""
        
        # Get base price from config
        config_response = self.db.table("pricing_config").select("*").eq("service_type", service_type).execute()
        
        if not config_response.data:
            base_price = 100.0
        else:
            base_price = config_response.data[0]["base_price"]
        
        # Urgency multiplier (1.0 to 1.5 for levels 1-5)
        urgency_multiplier = 1.0 + (urgency_level - 1) * 0.125
        
        estimated_price = base_price * urgency_multiplier
        
        return round(estimated_price, 2)

    async def _match_workers(
        self,
        task_id: str,
        service_type: str,
        location_lat: float,
        location_lng: float,
        limit: int = 5
    ) -> List[str]:
        """Find and match suitable workers for a task"""
        
        # Get verified workers offering this service type
        workers_response = self.db.table("workers").select("*").eq("is_verified", True).execute()
        
        if not workers_response.data:
            return []
        
        # Filter workers by service type and calculate distance
        suitable_workers = []
        
        for worker in workers_response.data:
            service_types = worker.get("service_types", [])
            
            # Check if worker offers this service
            if service_type not in service_types:
                continue
            
            # Calculate distance
            distance = haversine(
                location_lat, location_lng,
                worker.get("location_lat"), worker.get("location_lng")
            )
            
            suitable_workers.append({
                "worker_id": worker["worker_id"],
                "rating": worker.get("rating", 5.0),
                "distance": distance,
                "phone_number": worker["phone_number"]
            })
        
        # Sort by rating and distance
        suitable_workers.sort(key=lambda x: (-x["rating"], x["distance"]))
        
        # Take top 5 workers
        matched_workers = [w["worker_id"] for w in suitable_workers[:limit]]
        
        # Store matching data for later (could send notifications)
        # TODO: Send messages to workers
        
        return matched_workers

    # uses shared haversine utility

    async def assign_worker_to_task(
        self,
        task_id: str,
        worker_id: str
    ) -> Dict[str, Any]:
        """Assign a worker to a task"""
        
        response = self.db.table("tasks").update({
            "assigned_worker_id": worker_id,
            "status": TaskStatus.ASSIGNED.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to assign worker")

    async def get_task_details(self, task_id: str) -> Dict[str, Any]:
        """Get task with all related information"""
        
        response = self.db.table("tasks").select("*").eq("task_id", task_id).execute()
        
        if not response.data:
            raise Exception("Task not found")
        
        task = response.data[0]
        
        # Get customer info
        customer_response = self.db.table("customers").select("*").eq("user_id", task["customer_id"]).execute()
        if customer_response.data:
            task["customer"] = customer_response.data[0]
        
        # Get worker info if assigned
        if task.get("assigned_worker_id"):
            worker_response = self.db.table("workers").select("*").eq("worker_id", task["assigned_worker_id"]).execute()
            if worker_response.data:
                task["worker"] = worker_response.data[0]
        
        # Get tracking data if in progress
        if task["status"] in ["in_progress", "completed"]:
            tracking_response = self.db.table("tracking").select("*").eq("task_id", task_id).order("created_at", desc=True).execute()
            task["tracking"] = tracking_response.data or []
        
        return task

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus
    ) -> Dict[str, Any]:
        """Update task status"""
        
        response = self.db.table("tasks").update({
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to update task status")

    async def cancel_task(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        """Cancel a task"""
        
        response = self.db.table("tasks").update({
            "status": TaskStatus.CANCELLED.value,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to cancel task")
