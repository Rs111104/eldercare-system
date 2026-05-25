from __future__ import annotations

import logging
import time

from app.core.celery_app import get_celery
from app.core import metrics

logger = logging.getLogger("app.celery_tasks")

celery = get_celery()


if celery:
    from celery import signals

    _task_started_at: dict[str, float] = {}

    @signals.task_prerun.connect
    def task_prerun_handler(task_id=None, task=None, **kwargs):
        _task_started_at[task_id] = time.perf_counter()
        logger.info("celery_task_start", extra={"action": "celery.on_start", "status": "started", "task_id": task_id, "task_name": getattr(task, "name", ""), "retry_count": getattr(getattr(task, "request", None), "retries", 0)})

    @signals.task_success.connect
    def task_success_handler(sender=None, result=None, **kwargs):
        task_id = getattr(getattr(sender, "request", None), "id", "")
        elapsed = time.perf_counter() - _task_started_at.pop(task_id, time.perf_counter())
        logger.info("celery_task_success", extra={"action": "celery.on_success", "status": "success", "duration_ms": int(elapsed * 1000), "task_id": task_id, "task_name": getattr(sender, "name", ""), "retry_count": getattr(getattr(sender, "request", None), "retries", 0)})
        try:
            if metrics.CELERY_TASK_DURATION is not None:
                metrics.CELERY_TASK_DURATION.labels(task_name=getattr(sender, "name", ""), status="success").observe(elapsed)
        except Exception:
            pass

    @signals.task_failure.connect
    def task_failure_handler(task_id=None, exception=None, sender=None, **kwargs):
        elapsed = time.perf_counter() - _task_started_at.pop(task_id, time.perf_counter())
        logger.exception("celery_task_failure", extra={"action": "celery.on_failure", "status": "failure", "duration_ms": int(elapsed * 1000), "task_id": task_id, "task_name": getattr(sender, "name", ""), "retry_count": getattr(getattr(sender, "request", None), "retries", 0)})
        try:
            if metrics.CELERY_TASK_DURATION is not None:
                metrics.CELERY_TASK_DURATION.labels(task_name=getattr(sender, "name", ""), status="failure").observe(elapsed)
        except Exception:
            pass
        try:
            from app.store import store
            store.add_dead_letter(getattr(sender, "name", "unknown"), {}, exception.__class__.__name__ if exception else "unknown")
        except Exception:
            logger.exception("celery_dead_letter_failed")

    @celery.task(name="eldercare.send_whatsapp_message", autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
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

    @celery.task(name="eldercare.release_payout", autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
    def release_payout(payload: dict) -> dict:
        try:
            from app.store import store

            payout_id = payload.get("payout_id")
            payout = store.payouts.get(payout_id)
            if not payout:
                return {"status": "missing", "payout_id": payout_id}
            if payout.get("status") == "held":
                return {"status": "held", "payout_id": payout_id}
            payout["status"] = "released"
            payout["released_at"] = store._now()
            logger.info("payout_released", extra={"action": "payout.release", "status": "success", "payout_id": payout_id})
            return {"status": "released", "payout_id": payout_id}
        except Exception as e:
            logger.exception("Payout task failed: %s", e)
            raise

    @celery.task(name="eldercare.release_pending_payouts", autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
    def release_pending_payouts() -> dict:
        try:
            from app.store import store
            store.release_verification_payouts()
            return {"status": "ok"}
        except Exception as e:
            logger.exception("Failed to release pending payouts: %s", e)
            raise

    @celery.task(name="eldercare.weekly_ops_digest", autoretry_for=(Exception,), retry_backoff=True, retry_jitter=True, retry_kwargs={"max_retries": 3})
    def weekly_ops_digest() -> dict:
        from app.services.admin_intelligence import AdminIntelligenceService
        from app.services.whatsapp_service import WhatsAppService
        from app.store import store

        digest = AdminIntelligenceService().weekly_digest(store)
        admins = list(getattr(store, "admins", {}).values())
        if not admins:
            return {"status": "skipped", "reason": "no_admins", "digest": digest}
        content = (
            "Weekly ops digest\n"
            f"Completed: {digest['tasks_completed']}\n"
            f"Revenue: Rs {digest['revenue']:.2f}\n"
            f"Unmatched rate: {digest['unmatched_task_rate']:.2%}"
        )
        import asyncio

        service = WhatsAppService()
        for admin in admins:
            asyncio.get_event_loop().run_until_complete(service.send_text_message(admin["phone"], content))
        return {"status": "sent", "admin_count": len(admins), "digest": digest}
