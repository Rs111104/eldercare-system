"""
Worker integration and management
"""
from typing import List, Optional, Dict
from app.core.database import get_db
from supabase import Client
from datetime import datetime
from app.utils.geo import haversine


class WorkerIntegration:
    """Integration layer for worker management"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def get_worker_by_phone(self, phone_number: str) -> Optional[Dict]:
        """Find worker by phone number"""
        try:
            response = self.db.table("workers").select("*").eq("phone_number", phone_number).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error finding worker: {e}")
            return None
    
    async def get_workers_by_service_type(self, service_type: str, 
                                         latitude: float = None,
                                         longitude: float = None,
                                         radius_km: float = 10) -> List[Dict]:
        """Find workers by service type and optional location"""
        try:
            response = self.db.table("workers").select("*").eq(
                "service_types_contains", service_type
            ).eq("is_verified", True).execute()
            
            workers = response.data or []
            
            # Filter by distance if coordinates provided
            if latitude and longitude:
                from math import radians, sin, cos, sqrt, atan2
                
                filtered = []
                for worker in workers:
                    worker_lat = worker.get("location_lat")
                    worker_lng = worker.get("location_lng")
                    
                    if worker_lat and worker_lng:
                        distance = haversine(
                            latitude, longitude,
                            worker_lat, worker_lng
                        )
                        
                        if distance <= radius_km:
                            worker["distance"] = round(distance, 2)
                            filtered.append(worker)
                
                # Sort by distance
                filtered.sort(key=lambda w: w.get("distance", float('inf')))
                return filtered
            
            return workers
        except Exception as e:
            print(f"Error finding workers by service: {e}")
            return []
    
    async def update_worker_availability(self, worker_id: str, 
                                        is_available: bool) -> bool:
        """Update worker availability status"""
        try:
            response = self.db.table("workers").update({
                "is_available": is_available,
                "last_status_update": datetime.utcnow().isoformat()
            }).eq("worker_id", worker_id).execute()
            
            return bool(response.data)
        except Exception as e:
            print(f"Error updating availability: {e}")
            return False
    
    async def get_worker_earnings(self, worker_id: str, 
                                 days: int = 30) -> Dict:
        """Get worker earnings for period"""
        from datetime import timedelta
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            response = self.db.table("payouts").select("*").eq(
                "worker_id", worker_id
            ).gte("created_at", cutoff_date).execute()
            
            payouts = response.data or []
            
            return {
                "total_earnings": sum(p.get("total_amount", 0) for p in payouts),
                "completed_tasks": len(payouts),
                "average_per_task": sum(p.get("total_amount", 0) for p in payouts) / len(payouts) if payouts else 0,
                "period_days": days
            }
        except Exception as e:
            print(f"Error getting earnings: {e}")
            return {}
    
    async def get_worker_stats(self, worker_id: str) -> Dict:
        """Get comprehensive worker statistics"""
        try:
            # Get worker info
            worker_response = self.db.table("workers").select("*").eq("worker_id", worker_id).execute()
            if not worker_response.data:
                return {}
            
            worker = worker_response.data[0]
            
            # Get task stats
            tasks_response = self.db.table("tasks").select("*").eq("worker_id", worker_id).execute()
            tasks = tasks_response.data or []
            
            completed = len([t for t in tasks if t["status"] == "completed"])
            cancelled = len([t for t in tasks if t["status"] == "cancelled"])
            
            # Get reviews
            reviews_response = self.db.table("reviews").select("rating").eq("worker_id", worker_id).execute()
            reviews = reviews_response.data or []
            avg_rating = sum(r.get("rating", 0) for r in reviews) / len(reviews) if reviews else 0
            
            return {
                "worker_id": worker_id,
                "phone_number": worker.get("phone_number"),
                "is_verified": worker.get("is_verified", False),
                "service_types": worker.get("service_types", []),
                "rating": avg_rating,
                "total_tasks": len(tasks),
                "completed_tasks": completed,
                "cancelled_tasks": cancelled,
                "success_rate": f"{(completed/len(tasks)*100):.1f}%" if tasks else "0%",
                "total_reviews": len(reviews),
                "is_available": worker.get("is_available", True)
            }
        except Exception as e:
            print(f"Error getting worker stats: {e}")
            return {}
    
    # uses shared haversine utility


class WorkerRating:
    """Worker rating and review management"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def add_review(self, task_id: str, worker_id: str, customer_id: str,
                        rating: int, comment: str = "") -> bool:
        """Add review for worker"""
        try:
            review = {
                "task_id": task_id,
                "worker_id": worker_id,
                "customer_id": customer_id,
                "rating": min(5, max(1, rating)),  # Clamp 1-5
                "comment": comment,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.table("reviews").insert(review).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error adding review: {e}")
            return False
    
    async def get_worker_rating(self, worker_id: str) -> float:
        """Get average rating for worker"""
        try:
            response = self.db.table("reviews").select("rating").eq("worker_id", worker_id).execute()
            
            reviews = response.data or []
            if not reviews:
                return 0.0
            
            average = sum(r.get("rating", 0) for r in reviews) / len(reviews)
            return round(average, 1)
        except Exception as e:
            print(f"Error getting rating: {e}")
            return 0.0
    
    async def get_recent_reviews(self, worker_id: str, limit: int = 5) -> List[Dict]:
        """Get recent reviews for worker"""
        try:
            response = self.db.table("reviews").select("*").eq(
                "worker_id", worker_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            print(f"Error getting reviews: {e}")
            return []
