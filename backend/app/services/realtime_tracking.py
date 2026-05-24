"""
Real-time tracking with WebSocket support
"""
import json
from datetime import datetime
from typing import Set, Dict
from fastapi import WebSocket, WebSocketDisconnect
from app.core.database import get_db
from supabase import Client


class TrackingManager:
    """Manage real-time tracking connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.task_locations: Dict[str, Dict] = {}
    
    async def connect(self, task_id: str, websocket: WebSocket):
        """Accept a new connection"""
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        
        self.active_connections[task_id].add(websocket)
        
        # Send current location if available
        if task_id in self.task_locations:
            await websocket.send_json({
                "type": "current_location",
                "data": self.task_locations[task_id]
            })
    
    def disconnect(self, task_id: str, websocket: WebSocket):
        """Remove a connection"""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def broadcast(self, task_id: str, message: Dict):
        """Broadcast message to all connected clients for a task"""
        if task_id in self.active_connections:
            disconnected = set()
            
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(task_id, connection)
    
    async def update_location(self, task_id: str, worker_id: str, 
                             latitude: float, longitude: float):
        """Update worker location and broadcast"""
        location_data = {
            "task_id": task_id,
            "worker_id": worker_id,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store current location
        self.task_locations[task_id] = location_data
        
        # Broadcast to all subscribers
        await self.broadcast(task_id, {
            "type": "location_update",
            "data": location_data
        })
    
    async def send_event(self, task_id: str, event_type: str, data: Dict):
        """Send task event to subscribers"""
        message = {
            "type": event_type,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        await self.broadcast(task_id, message)
    
    async def notify_status_change(self, task_id: str, new_status: str, 
                                   worker_id: str = None):
        """Notify subscribers of task status change"""
        await self.send_event(task_id, "status_changed", {
            "new_status": new_status,
            "worker_id": worker_id
        })
    
    async def notify_worker_checked_in(self, task_id: str, worker_id: str):
        """Notify that worker has checked in"""
        await self.send_event(task_id, "worker_checked_in", {
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_worker_checked_out(self, task_id: str, worker_id: str):
        """Notify that worker has checked out"""
        await self.send_event(task_id, "worker_checked_out", {
            "worker_id": worker_id,
            "timestamp": datetime.utcnow().isoformat()
        })


class LocationTracker:
    """Handle location tracking and distance calculations"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def record_location(self, task_id: str, worker_id: str, 
                             latitude: float, longitude: float, 
                             accuracy: float = None):
        """Record location point for tracking"""
        try:
            tracking_entry = {
                "task_id": task_id,
                "worker_id": worker_id,
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "event_type": "location_update",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.table("tracking").insert(tracking_entry).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Error recording location: {e}")
            return False
    
    async def get_location_history(self, task_id: str, limit: int = 100) -> list:
        """Get location history for a task"""
        try:
            response = self.db.table("tracking").select("*").eq("task_id", task_id).order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting location history: {e}")
            return []
    
    async def calculate_distance_traveled(self, task_id: str) -> float:
        """Calculate total distance traveled during task"""
        history = await self.get_location_history(task_id)
        
        if len(history) < 2:
            return 0.0
        
        total_distance = 0.0
        
        for i in range(len(history) - 1):
            current = history[i]
            next_point = history[i + 1]
            
            distance = self._haversine_distance(
                current["latitude"], current["longitude"],
                next_point["latitude"], next_point["longitude"]
            )
            total_distance += distance
        
        return round(total_distance, 2)
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    async def get_current_location(self, task_id: str) -> Dict:
        """Get most recent location for task"""
        try:
            response = self.db.table("tracking").select("*").eq("task_id", task_id).eq("event_type", "location_update").order("created_at", desc=True).limit(1).execute()
            
            if response.data:
                location = response.data[0]
                return {
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "accuracy": location.get("accuracy"),
                    "timestamp": location["created_at"]
                }
            return {}
        except Exception as e:
            print(f"Error getting current location: {e}")
            return {}


# Global tracking manager instance
tracking_manager = TrackingManager()


async def handle_tracking_websocket(task_id: str, websocket: WebSocket, 
                                   db: Client):
    """Handle WebSocket connection for task tracking"""
    await tracking_manager.connect(task_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "location_update":
                location = data.get("data", {})
                await tracking_manager.update_location(
                    task_id,
                    location.get("worker_id"),
                    location.get("latitude"),
                    location.get("longitude")
                )
            
            elif data.get("type") == "subscribe":
                # Client subscribed, send acknowledgment
                await websocket.send_json({
                    "type": "subscribed",
                    "task_id": task_id
                })
    
    except WebSocketDisconnect:
        tracking_manager.disconnect(task_id, websocket)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        tracking_manager.disconnect(task_id, websocket)
