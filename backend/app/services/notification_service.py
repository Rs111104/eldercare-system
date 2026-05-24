"""
Notification service - handle communications to users
"""
from app.services.whatsapp_service import WhatsAppService
from typing import Optional

class NotificationService:
    def __init__(self):
        self.whatsapp = WhatsAppService()

    async def notify_task_created(
        self,
        customer_phone: str,
        customer_name: str,
        task_title: str,
        estimated_price: float
    ) -> bool:
        """Notify customer that task has been created"""
        
        message = f"Hi {customer_name}! Your task '{task_title}' has been created. Estimated cost: ₹{estimated_price}. Workers are being matched..."
        return await self.whatsapp.send_text_message(customer_phone, message)

    async def notify_worker_assigned(
        self,
        customer_phone: str,
        worker_name: str,
        worker_phone: str,
        estimated_arrival_minutes: int
    ) -> bool:
        """Notify customer that worker has been assigned"""
        
        message = f"Great! {worker_name} has been assigned to your task. They will arrive in approximately {estimated_arrival_minutes} minutes. Contact: {worker_phone}"
        return await self.whatsapp.send_text_message(customer_phone, message)

    async def notify_task_in_progress(
        self,
        customer_phone: str,
        worker_name: str,
        worker_phone: str
    ) -> bool:
        """Notify customer that task has started"""
        
        message = f"{worker_name} has arrived and started working on your task. You can reach them at {worker_phone}"
        return await self.whatsapp.send_text_message(customer_phone, message)

    async def notify_task_completed(
        self,
        customer_phone: str,
        worker_name: str,
        total_amount: float,
        notes: str = ""
    ) -> bool:
        """Notify customer that task is completed"""
        
        message = f"Task completed by {worker_name}! Total amount: ₹{total_amount}. "
        if notes:
            message += f"Notes: {notes} "
        message += "Thank you for using ElderCare!"
        
        return await self.whatsapp.send_text_message(customer_phone, message)

    async def notify_payout_processed(
        self,
        worker_phone: str,
        amount: float,
        payout_type: str = "immediate"  # immediate or verification
    ) -> bool:
        """Notify worker about payout"""
        
        if payout_type == "immediate":
            message = f"Great work! ₹{amount} has been transferred to your account immediately."
        else:
            message = f"Task verification complete! ₹{amount} (final payment) has been transferred to your account."
        
        return await self.whatsapp.send_text_message(worker_phone, message)

    async def notify_worker_new_task(
        self,
        worker_phone: str,
        task_title: str,
        task_description: str,
        estimated_price: float,
        urgency_level: int
    ) -> bool:
        """Alert worker about new available task"""
        
        urgency_text = "🚨 URGENT!" if urgency_level >= 4 else "New Task" if urgency_level >= 3 else "Task Available"
        
        message = f"{urgency_text}\n{task_title}\n{task_description}\nReward: ₹{estimated_price}\n\nAccept or Reject?"
        
        return await self.whatsapp.send_text_message(worker_phone, message)
