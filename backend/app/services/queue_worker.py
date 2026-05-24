from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from app.config import settings
from app.store import store
from app.services.whatsapp_service import WhatsAppService

logger = logging.getLogger("app.queue_worker")


class QueueWorker:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._stop_event = asyncio.Event()

    async def _process_message(self, message: dict):
        try:
            # If Celery is available, dispatch a background task for outbound messages.
            try:
                from app.services.celery_tasks import send_whatsapp_message
                celery_task = send_whatsapp_message
            except Exception:
                celery_task = None

            if message.get("direction") == "out":
                if celery_task is not None:
                    try:
                        celery_task.delay({"phone": message.get("phone"), "content": message.get("content"), "message_type": message.get("message_type", "text")})
                        message["processed"] = True
                    except Exception:
                        # fallback to direct send
                        ws = WhatsAppService()
                        await ws.send_message(phone=message.get("phone"), content=message.get("content"), message_type=message.get("message_type", "text"))
                        message["processed"] = True
                else:
                    ws = WhatsAppService()
                    await ws.send_message(phone=message.get("phone"), content=message.get("content"), message_type=message.get("message_type", "text"))
                    message["processed"] = True
            else:
                # inbound messages might be processed elsewhere; mark processed
                message["processed"] = True
        except Exception:
            logger.exception("Failed to process queued message")

    async def _run_redis_loop(self, url: str):
        try:
            import redis.asyncio as aioredis
        except Exception:
            logger.warning("aioredis not available; cannot run Redis queue loop")
            return
        try:
            client = aioredis.from_url(url, decode_responses=True)
            # Prefer reading from Redis Stream 'whatsapp:stream' for durability
            last_id = "$"
            while not self._stop_event.is_set():
                try:
                    # XREAD BLOCK 5000
                    resp = await client.xread({"whatsapp:stream": last_id}, block=5000, count=1)
                    if not resp:
                        # fallback to list (for compatibility)
                        item = await client.brpop("whatsapp:queue", timeout=1)
                        if not item:
                            continue
                        _, raw = item
                        msg = json.loads(raw)
                        await self._process_message(msg)
                        continue

                    # resp is list of (stream, [(id, {field: value})])
                    for stream_name, entries in resp:
                        for entry_id, fields in entries:
                            raw = fields.get("data") or ""
                            try:
                                msg = json.loads(raw)
                            except Exception:
                                msg = {}
                            await self._process_message(msg)
                            last_id = entry_id
                except asyncio.CancelledError:
                    break
                except Exception:
                    logger.exception("Error in Redis queue loop")
                    await asyncio.sleep(1)
        except Exception:
            logger.exception("Failed to start Redis client")

    async def _run_inmemory_loop(self):
        while not self._stop_event.is_set():
            try:
                pending = [m for m in list(store.whatsapp_messages) if not m.get("processed")]
                for msg in pending:
                    await self._process_message(msg)
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in in-memory queue loop")
                await asyncio.sleep(1)

    async def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        if settings.REDIS_URL:
            logger.info("Starting Redis-backed queue worker")
            self._task = asyncio.create_task(self._run_redis_loop(settings.REDIS_URL))
        else:
            logger.info("Starting in-memory queue worker")
            self._task = asyncio.create_task(self._run_inmemory_loop())

    async def stop(self):
        if not self._running:
            return
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
        self._running = False


_worker: Optional[QueueWorker] = None


async def start_queue_worker(app):
    global _worker
    if _worker is None:
        _worker = QueueWorker()
        await _worker.start()
        app.state.queue_worker = _worker


async def stop_queue_worker(app):
    global _worker
    if _worker is not None:
        await _worker.stop()
        _worker = None
