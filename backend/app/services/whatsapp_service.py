from __future__ import annotations

from app.config import settings
from app.store import store
from app.core import metrics
from app.core.retry import retry_async
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        # Expect signature header like 'sha256=...'
        # For security, webhook verification requires WHATSAPP_APP_SECRET to be set
        if not settings.WHATSAPP_APP_SECRET:
            raise RuntimeError("WHATSAPP_APP_SECRET is not configured")
        try:
            import hmac
            import hashlib
            if not signature:
                return False
            if signature.startswith("sha256="):
                sig = signature.split("=", 1)[1]
            else:
                sig = signature
            computed = hmac.new(settings.WHATSAPP_APP_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
            return computed == sig
        except Exception:
            return False

    async def send_text_message(self, phone_number: str, message: str) -> bool:
        # Store outbound message locally first (queued for delivery)
        msg = store.store_whatsapp_message(phone=phone_number, direction="out", message_type="text", content=message)

        if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            # No real provider configured; message queued locally
            logger.info("whatsapp_message_queued", extra={"action": "whatsapp.send", "status": "queued"})
            self._record_metric("queued", "text")
            return True

        @retry_async(retries=3)
        async def _post_message(payload: dict):
            url = f"https://graph.facebook.com/v16.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=10) as resp:
                    text = await resp.text()
                    if resp.status >= 400:
                        raise Exception(f"WhatsApp send failed: {resp.status} {text}")
                    return await resp.json()

        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message},
        }

        try:
            await _post_message(payload)
            # mark stored message as processed
            msg["processed"] = True
            self._record_metric("sent", "text")
            return True
        except Exception as e:
            logger.exception("whatsapp_delivery_failed", extra={"action": "whatsapp.send", "status": "failed"})
            self._record_metric("failed", "text")
            try:
                store.add_dead_letter("whatsapp.send_text_message", {"message_id": msg["id"], "message_type": "text"}, e.__class__.__name__)
            except Exception:
                logger.exception("dead_letter_record_failed")
            return False

    async def send_message(self, phone: str, content: str, message_type: str = "text") -> dict:
        delivered = await self.send_text_message(phone, content)
        return {"status": "sent" if delivered else "failed", "message_type": message_type}

    def _record_metric(self, status: str, message_type: str) -> None:
        try:
            if metrics.WHATSAPP_MESSAGES_SENT is not None:
                metrics.WHATSAPP_MESSAGES_SENT.labels(status=status, message_type=message_type).inc()
        except Exception:
            pass

    async def send_location_in_progress_message(self, phone_number: str, worker_name: str, worker_phone: str) -> bool:
        return await self.send_text_message(phone_number, f"Your helper {worker_name} is on the way. Phone: {worker_phone}")

    async def send_task_completed_message(self, phone_number: str, amount: float, worker_name: str) -> bool:
        return await self.send_text_message(phone_number, f"Task completed by {worker_name}. Amount: ₹{amount}")

    async def send_worker_assignment_message(self, worker_phone: str, customer_name: str, task_title: str, location: str) -> bool:
        return await self.send_text_message(worker_phone, f"New task from {customer_name}: {task_title} at {location}")

    def process_incoming_message(self, message_data: dict):
        return message_data

    async def download_media(self, media_id: str, media_type: str = "audio"):
        if not settings.WHATSAPP_ACCESS_TOKEN:
            return f"media:{media_id}".encode("utf-8")

        @retry_async(retries=3)
        async def _download(media_id_inner: str):
            url = f"https://graph.facebook.com/v16.0/{media_id_inner}"
            headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    if resp.status >= 400:
                        raise Exception(f"Failed to download media: {resp.status}")
                    data = await resp.read()
                    return data

        try:
            return await _download(media_id)
        except Exception as e:
            logger.exception("whatsapp_media_download_failed")
            return None
