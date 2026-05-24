"""
Worker service - manage worker profiles and operations
"""
from datetime import datetime
from app.core.database import get_db
from supabase import Client
from typing import List, Dict, Any, Optional

class WorkerService:
    def __init__(self, db: Client):
        self.db = db

    async def get_available_tasks(
        self,
        worker_id: str,
        service_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get available tasks for a worker"""
        
        # Get worker info
        worker_response = self.db.table("workers").select("*").eq("worker_id", worker_id).execute()
        
        if not worker_response.data:
            raise Exception("Worker not found")
        
        worker = worker_response.data[0]
        service_types = worker.get("service_types", [])
        
        # Get unassigned tasks that match service types
        query = self.db.table("tasks").select("*").eq("status", "created")
        
        if service_type:
            # Filter by specific service type
            tasks_response = query.contains("preferred_service_types", [service_type]).order("created_at", desc=True).limit(limit).execute()
        else:
            tasks_response = query.order("created_at", desc=True).limit(limit * 2).execute()
        
        if not tasks_response.data:
            return []
        
        # Filter tasks that match worker's service types
        available_tasks = []
        for task in tasks_response.data:
            preferred_services = task.get("preferred_service_types", [])
            # Check if worker has any of the preferred services
            if any(service in service_types for service in preferred_services or [task["task_type"]]):
                available_tasks.append(task)
                if len(available_tasks) >= limit:
                    break
        
        return available_tasks

    async def accept_task(
        self,
        worker_id: str,
        task_id: str
    ) -> Dict[str, Any]:
        """Worker accepts a task"""
        
        # Verify task is still available
        task_response = self.db.table("tasks").select("*").eq("task_id", task_id).execute()
        
        if not task_response.data:
            raise Exception("Task not found")
        
        task = task_response.data[0]
        
        if task["status"] != "created":
            raise Exception("Task is no longer available")
        
        # Assign worker to task
        update_response = self.db.table("tasks").update({
            "assigned_worker_id": worker_id,
            "status": "accepted",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if update_response.data:
            return update_response.data[0]
        
        raise Exception("Failed to accept task")

    async def reject_task(self, worker_id: str, task_id: str) -> bool:
        """Worker rejects a task"""
        # TODO: Add logic to track rejections and prevent spam
        return True

    async def check_in(
        self,
        worker_id: str,
        task_id: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Worker checks in at task location"""
        
        # Create tracking record
        tracking_response = self.db.table("tracking").insert({
            "task_id": task_id,
            "worker_id": worker_id,
            "event_type": "check_in",
            "latitude": latitude,
            "longitude": longitude
        }).execute()
        
        # Update task status
        task_response = self.db.table("tasks").update({
            "status": "in_progress",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if tracking_response.data:
            return tracking_response.data[0]
        
        raise Exception("Failed to check in")

    async def check_out(
        self,
        worker_id: str,
        task_id: str,
        latitude: float,
        longitude: float,
        report: str,
        proof_photos: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Worker checks out and completes task"""
        
        # Create tracking record
        tracking_response = self.db.table("tracking").insert({
            "task_id": task_id,
            "worker_id": worker_id,
            "event_type": "check_out",
            "latitude": latitude,
            "longitude": longitude,
            "report": report,
            "proof_photos": proof_photos or []
        }).execute()
        
        # Update task status to completed
        task_response = self.db.table("tasks").update({
            "status": "completed",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("task_id", task_id).execute()
        
        if tracking_response.data and task_response.data:
            # Trigger payout processing
            await self._process_payout(task_id, worker_id)
            return tracking_response.data[0]
        
        raise Exception("Failed to check out")

    async def _process_payout(self, task_id: str, worker_id: str) -> None:
        """Process payout for completed task"""
        
        # Get task details
        task_response = self.db.table("tasks").select("*").eq("task_id", task_id).execute()
        
        if not task_response.data:
            return
        
        task = task_response.data[0]
        total_amount = task.get("actual_price") or task.get("estimated_price", 0)
        
        # Create payout record (75% immediate, 25% after verification)
        self.db.table("payouts").insert({
            "task_id": task_id,
            "worker_id": worker_id,
            "immediate_payout": total_amount * 0.75,
            "verification_payout": total_amount * 0.25,
            "total_amount": total_amount,
            "status": "pending"
        }).execute()

    async def get_worker_stats(self, worker_id: str) -> Dict[str, Any]:
        """Get worker statistics and performance metrics"""
        
        # Get completed tasks
        completed_tasks = self.db.table("tasks").select("*").eq("assigned_worker_id", worker_id).eq("status", "completed").execute()
        
        # Get reviews and ratings
        reviews = self.db.table("reviews").select("*").eq("worker_id", worker_id).execute()
        
        total_tasks = len(completed_tasks.data) if completed_tasks.data else 0
        
        # Calculate average rating
        avg_rating = 5.0
        if reviews.data:
            avg_rating = sum(r["rating"] for r in reviews.data) / len(reviews.data)
        
        return {
            "total_tasks": total_tasks,
            "average_rating": round(avg_rating, 1),
            "reviews_count": len(reviews.data) if reviews.data else 0,
            "completion_rate": self._calculate_completion_rate(worker_id)
        }

    async def _calculate_completion_rate(self, worker_id: str) -> float:
        """Calculate worker's task completion rate"""
        
        assigned_tasks = self.db.table("tasks").select("*").eq("assigned_worker_id", worker_id).execute()
        
        if not assigned_tasks.data:
            return 0.0
        
        completed = sum(1 for t in assigned_tasks.data if t["status"] == "completed")
        
        return round((completed / len(assigned_tasks.data)) * 100, 2)

    async def update_location(
        self,
        worker_id: str,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Update worker's current location"""
        
        response = self.db.table("workers").update({
            "location_lat": latitude,
            "location_lng": longitude
        }).eq("worker_id", worker_id).execute()
        
        if response.data:
            return response.data[0]
        
        raise Exception("Failed to update location")
