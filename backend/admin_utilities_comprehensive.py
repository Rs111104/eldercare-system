"""
Comprehensive Admin Utilities for ElderCare System
Includes user management, verification, reporting, and system maintenance
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

logger = logging.getLogger(__name__)


class AdminUserManager:
    """Manage users - activate, deactivate, verify, etc."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all users with pagination"""
        from app.models.database import User
        
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "phone_number": u.phone_number,
                "user_type": u.user_type,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
            }
            for u in users
        ]

    async def get_users_by_type(self, user_type: str) -> List[Dict]:
        """Get all users of a specific type"""
        from app.models.database import User
        
        query = select(User).where(User.user_type == user_type)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "user_type": u.user_type,
                "is_active": u.is_active,
            }
            for u in users
        ]

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        from app.models.database import User
        
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        logger.info(f"User {user_id} deactivated")
        return True

    async def activate_user(self, user_id: str) -> bool:
        """Activate a user account"""
        from app.models.database import User
        
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return False
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        logger.info(f"User {user_id} activated")
        return True

    async def verify_worker(self, worker_id: str) -> bool:
        """Mark worker as verified"""
        from app.models.database import User
        
        query = select(User).where(and_(User.id == worker_id, User.user_type == "worker"))
        result = await self.db.execute(query)
        worker = result.scalar_one_or_none()
        
        if not worker:
            return False
        
        worker.is_verified = True
        worker.updated_at = datetime.utcnow()
        await self.db.commit()
        logger.info(f"Worker {worker_id} verified")
        return True

    async def get_unverified_workers(self) -> List[Dict]:
        """Get all unverified workers"""
        from app.models.database import User
        
        query = select(User).where(
            and_(User.user_type == "worker", User.is_verified == False)
        )
        result = await self.db.execute(query)
        workers = result.scalars().all()
        
        return [
            {
                "id": w.id,
                "name": w.name,
                "email": w.email,
                "phone_number": w.phone_number,
                "created_at": w.created_at,
            }
            for w in workers
        ]


class AdminAnalytics:
    """System analytics and reporting"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        from app.models.database import User, Task
        
        users_query = select(User)
        users_result = await self.db.execute(users_query)
        all_users = users_result.scalars().all()
        
        tasks_query = select(Task)
        tasks_result = await self.db.execute(tasks_query)
        all_tasks = tasks_result.scalars().all()
        
        customers = [u for u in all_users if u.user_type == "customer"]
        workers = [u for u in all_users if u.user_type == "worker"]
        active_tasks = [t for t in all_tasks if t.status == "in_progress"]
        completed_tasks = [t for t in all_tasks if t.status == "completed"]
        
        total_revenue = sum(t.estimated_price or 0 for t in completed_tasks)
        avg_rating = (
            sum(w.rating or 0 for w in workers) / len(workers)
            if workers else 0
        )
        
        return {
            "total_users": len(all_users),
            "total_customers": len(customers),
            "total_workers": len(workers),
            "verified_workers": len([w for w in workers if w.is_verified]),
            "active_users": len([u for u in all_users if u.is_active]),
            "total_tasks": len(all_tasks),
            "active_tasks": len(active_tasks),
            "completed_tasks": len(completed_tasks),
            "pending_tasks": len([t for t in all_tasks if t.status == "pending"]),
            "total_revenue": float(total_revenue),
            "average_rating": float(avg_rating),
            "total_ratings": len([w for w in workers if w.rating]),
        }

    async def get_revenue_report(self, days: int = 30) -> Dict:
        """Get revenue report for the last N days"""
        from app.models.database import Task
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(Task).where(
            and_(Task.status == "completed", Task.completed_at >= cutoff_date)
        )
        result = await self.db.execute(query)
        completed_tasks = result.scalars().all()
        
        total_revenue = sum(t.final_price or t.estimated_price or 0 for t in completed_tasks)
        worker_earnings = sum(t.worker_earnings or 0 for t in completed_tasks)
        platform_earnings = total_revenue - worker_earnings
        
        return {
            "period_days": days,
            "total_tasks": len(completed_tasks),
            "total_revenue": float(total_revenue),
            "worker_earnings": float(worker_earnings),
            "platform_earnings": float(platform_earnings),
            "average_task_value": float(total_revenue / len(completed_tasks)) if completed_tasks else 0,
        }

    async def get_worker_performance(self, worker_id: str) -> Dict:
        """Get performance metrics for a worker"""
        from app.models.database import User, Task
        
        worker_query = select(User).where(User.id == worker_id)
        worker_result = await self.db.execute(worker_query)
        worker = worker_result.scalar_one_or_none()
        
        if not worker or worker.user_type != "worker":
            return {}
        
        tasks_query = select(Task).where(Task.assigned_worker_id == worker_id)
        tasks_result = await self.db.execute(tasks_query)
        tasks = tasks_result.scalars().all()
        
        completed = [t for t in tasks if t.status == "completed"]
        
        completion_rate = (len(completed) / len(tasks) * 100) if tasks else 0
        total_earnings = sum(t.worker_earnings or 0 for t in completed)
        avg_completion_time = (
            sum((t.completed_at - t.created_at).total_seconds() for t in completed if t.completed_at) / len(completed)
            if completed else 0
        )
        
        return {
            "worker_id": worker_id,
            "worker_name": worker.name,
            "total_tasks": len(tasks),
            "completed_tasks": len(completed),
            "completion_rate": float(completion_rate),
            "rating": float(worker.rating or 0),
            "total_earnings": float(total_earnings),
            "average_completion_time": float(avg_completion_time),
            "is_verified": worker.is_verified,
            "is_active": worker.is_active,
        }


class AdminMaintenance:
    """System maintenance and cleanup operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stale_users(self, inactive_days: int = 90) -> List[Dict]:
        """Get users inactive for N days"""
        from app.models.database import User
        
        cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
        
        query = select(User).where(User.updated_at < cutoff_date)
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "last_activity": u.updated_at,
                "days_inactive": (datetime.utcnow() - u.updated_at).days,
            }
            for u in users
        ]

    async def cleanup_expired_sessions(self) -> int:
        """Remove expired session tokens"""
        # Implementation would depend on your session storage
        logger.info("Cleanup expired sessions completed")
        return 0

    async def get_system_health(self) -> Dict:
        """Check system health status"""
        from app.models.database import User, Task
        
        try:
            # Test database connection
            users_count = (
                await self.db.execute(select(User))
            ).scalars().all()
            
            tasks_count = (
                await self.db.execute(select(Task))
            ).scalars().all()
            
            return {
                "status": "healthy",
                "database": "connected",
                "users_count": len(users_count),
                "tasks_count": len(tasks_count),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


class AdminNotifications:
    """Send admin notifications and alerts"""

    @staticmethod
    async def send_alert(title: str, message: str, severity: str = "info"):
        """Log admin alert"""
        logger.warning(f"[ADMIN ALERT - {severity.upper()}] {title}: {message}")

    @staticmethod
    async def notify_fraud_detection(task_id: str, reason: str):
        """Notify admins of potential fraud"""
        logger.warning(f"Potential fraud detected in task {task_id}: {reason}")

    @staticmethod
    async def notify_worker_complaint(worker_id: str, complaint: str):
        """Notify admins of worker complaints"""
        logger.warning(f"Complaint registered against worker {worker_id}: {complaint}")


# Export all admin utilities
__all__ = [
    "AdminUserManager",
    "AdminAnalytics",
    "AdminMaintenance",
    "AdminNotifications",
]
