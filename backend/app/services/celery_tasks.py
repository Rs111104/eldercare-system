from __future__ import annotations

import logging
from typing import Any

from app.core.celery_app import get_celery

logger = logging.getLogger("app.celery_tasks")

celery = get_celery()


if celery:
    @celery.task(name="eldercare.send_whatsapp_message")
    def send_whatsapp_message(payload: dict) -> dict:
        try:
            from app.services.whatsapp_service import WhatsAppService
            ws = WhatsAppService()
            # use sync send via aiohttp inside; this task runs in worker process
            import asyncio
            return asyncio.get_event_loop().run_until_complete(ws.send_message(phone=payload.get("phone"), content=payload.get("content"), message_type=payload.get("message_type", "text")))
        except Exception as e:
            logger.exception("Celery task failed: %s", e)
            raise

    @celery.task(name="eldercare.release_payout")
    def release_payout(payload: dict) -> dict:
        try:
            # placeholder for payout release integration
            logger.info("Releasing payout: %s", payload)
            return {"status": "ok", "payout_id": payload.get("payout_id")}
        except Exception as e:
            logger.exception("Payout task failed: %s", e)
            raise

    @celery.task(name="eldercare.release_pending_payouts")
    def release_pending_payouts() -> dict:
        try:
            from app.store import store
            store.release_verification_payouts()
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Failed to release pending payouts: %s", e)
            raise
*** End Patch