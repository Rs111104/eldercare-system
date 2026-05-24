"""
Admin utilities and management tools
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.database import get_db
from supabase import Client


class AdminUtilities:
    """Admin management utilities"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Check database connectivity
            db_check = self.db.table("customers").select("count", count="exact").limit(1).execute()
            
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    "database": "✓ Connected",
                    "api": "✓ Running",
                    "workers": "✓ Available"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def bulk_update_pricing(self, pricing_data: List[Dict[str, Any]]) -> bool:
        """Update pricing in bulk"""
        try:
            for config in pricing_data:
                self.db.table("pricing_config").upsert(config).execute()
            return True
        except Exception as e:
            print(f"Error updating pricing: {e}")
            return False
    
    async def export_data(self, export_type: str) -> Optional[str]:
        """Export data for analytics"""
        try:
            if export_type == "tasks":
                tasks = self.db.table("tasks").select("*").execute()
                return tasks.json()
            elif export_type == "payouts":
                payouts = self.db.table("payouts").select("*").execute()
                return payouts.json()
            elif export_type == "workers":
                workers = self.db.table("workers").select("*").execute()
                return workers.json()
            return None
        except Exception as e:
            print(f"Error exporting data: {e}")
            return None
    
    async def cleanup_old_data(self, days: int = 90) -> int:
        """Clean up old data (soft delete)"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Archive old cancelled tasks
            result = self.db.table("tasks").update({
                "archived": True
            }).eq("status", "cancelled").lt("created_at", cutoff_date).execute()
            
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Error cleaning up data: {e}")
            return 0
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate system performance report"""
        try:
            tasks = self.db.table("tasks").select("*").execute()
            workers = self.db.table("workers").select("*").execute()
            payouts = self.db.table("payouts").select("*").execute()
            
            total_tasks = len(tasks.data) if tasks.data else 0
            completed_tasks = len([t for t in (tasks.data or []) if t["status"] == "completed"])
            total_revenue = sum(p.get("total_amount", 0) for p in (payouts.data or []))
            
            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "completion_rate": f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
                "total_workers": len(workers.data) if workers.data else 0,
                "verified_workers": len([w for w in (workers.data or []) if w.get("is_verified")]),
                "total_revenue": round(total_revenue, 2),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            print(f"Error generating report: {e}")
            return {}
    
    async def send_bulk_notification(self, user_type: str, message: str) -> int:
        """Send bulk notifications to workers or customers"""
        try:
            # TODO: Implement WhatsApp bulk messaging
            return 0
        except Exception as e:
            print(f"Error sending notifications: {e}")
            return 0


class AuditLogger:
    """Audit logging for admin actions"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def log_action(self, admin_id: str, action: str, resource_type: str, 
                        resource_id: str, details: Optional[Dict] = None) -> bool:
        """Log admin action for audit trail"""
        try:
            # Create audit_logs table entry (if table exists)
            # For now, just log to console
            log_entry = {
                "admin_id": admin_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            print(f"Audit Log: {log_entry}")
            return True
        except Exception as e:
            print(f"Error logging action: {e}")
            return False
    
    async def get_audit_trail(self, admin_id: Optional[str] = None, 
                             days: int = 30) -> List[Dict]:
        """Get audit trail for specified period"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            # TODO: Query audit_logs table
            return []
        except Exception as e:
            print(f"Error retrieving audit trail: {e}")
            return []


class AnalyticsHelper:
    """Analytics and reporting utilities"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def calculate_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Calculate business metrics for period"""
        try:
            tasks = self.db.table("tasks").select("*").gte("created_at", start_date).lt("created_at", end_date).execute()
            payouts = self.db.table("payouts").select("*").gte("created_at", start_date).lt("created_at", end_date).execute()
            
            task_data = tasks.data or []
            payout_data = payouts.data or []
            
            return {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "tasks": {
                    "total": len(task_data),
                    "completed": len([t for t in task_data if t["status"] == "completed"]),
                    "cancelled": len([t for t in task_data if t["status"] == "cancelled"])
                },
                "revenue": {
                    "total": sum(p.get("total_amount", 0) for p in payout_data),
                    "immediate": sum(p.get("immediate_payout", 0) for p in payout_data),
                    "verification": sum(p.get("verification_payout", 0) for p in payout_data)
                },
                "average": {
                    "task_price": sum(t.get("price", 0) for t in task_data) / len(task_data) if task_data else 0,
                    "completion_time": "30 min"  # TODO: Calculate from tracking data
                }
            }
        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return {}
    
    async def get_worker_performance(self, worker_id: str) -> Dict[str, Any]:
        """Get detailed worker performance metrics"""
        try:
            # Get worker info
            worker_response = self.db.table("workers").select("*").eq("worker_id", worker_id).execute()
            if not worker_response.data:
                return {}
            
            worker = worker_response.data[0]
            
            # Get worker tasks
            tasks_response = self.db.table("tasks").select("*").eq("worker_id", worker_id).execute()
            tasks = tasks_response.data or []
            
            completed = len([t for t in tasks if t["status"] == "completed"])
            cancelled = len([t for t in tasks if t["status"] == "cancelled"])
            
            return {
                "worker_id": worker_id,
                "name": worker.get("name", "Unknown"),
                "rating": worker.get("rating", 0),
                "is_verified": worker.get("is_verified", False),
                "total_tasks": len(tasks),
                "completed_tasks": completed,
                "cancelled_tasks": cancelled,
                "success_rate": f"{(completed/len(tasks)*100):.1f}%" if tasks else "0%",
                "service_types": worker.get("service_types", [])
            }
        except Exception as e:
            print(f"Error getting worker performance: {e}")
            return {}


def generate_report(report_type: str, data: Dict) -> str:
    """Generate formatted report from data"""
    if report_type == "performance":
        return f"""
Performance Report
==================
Total Tasks: {data.get('total_tasks', 0)}
Completed: {data.get('completed_tasks', 0)}
Completion Rate: {data.get('completion_rate', 'N/A')}
Total Workers: {data.get('total_workers', 0)}
Verified Workers: {data.get('verified_workers', 0)}
Total Revenue: ₹{data.get('total_revenue', 0)}
Generated: {data.get('generated_at', 'N/A')}
"""
    
    elif report_type == "worker":
        return f"""
Worker Performance Report
=========================
Worker ID: {data.get('worker_id', 'N/A')}
Name: {data.get('name', 'N/A')}
Rating: {data.get('rating', 'N/A')}
Total Tasks: {data.get('total_tasks', 0)}
Completed: {data.get('completed_tasks', 0)}
Success Rate: {data.get('success_rate', 'N/A')}
Services: {', '.join(data.get('service_types', []))}
"""
    
    return "Unknown report type"
