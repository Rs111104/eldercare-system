from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Depends
import json
from app.services.whatsapp_service import WhatsAppService

from app.config import settings
from app.models import WhatsAppWebhookRequest
from app.store import store
from app.core.utils import sanitize_text
from app.services.whatsapp_service import WhatsAppService
from app.core.deps import require_role
from app.services.voice_service import VoiceProcessingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/webhook")
async def verify_whatsapp_webhook(request: Request):
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(challenge or 0)
    raise HTTPException(status_code=403, detail="Invalid verification token")


@router.post("/webhook")
async def handle_whatsapp_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    ws = WhatsAppService()
    if not ws.verify_webhook_signature(signature, body):
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    payload = WhatsAppWebhookRequest.model_validate(data)

    # sanitize content
    clean_content = sanitize_text(payload.content)
    msg = store.store_whatsapp_message(phone=payload.phone, direction="in", message_type=payload.message_type, content=clean_content, task_id=payload.task_id)

    try:
        if payload.message_type == "audio":
            task = store.create_task(customer_id=payload.phone, service_type="help", description=clean_content, urgency=1.25, base_price=150.0, distance_km=0.0, voice_note_url=clean_content)
            msg["processed"] = True
            return {"status": "received", "task_created": task}

        if payload.message_type == "text":
            v = VoiceProcessingService()
            classification = await v.classify_voice_request(clean_content)
            msg["processed"] = True
            return {"status": "received", "classification": classification}

        msg["processed"] = True
        return {"status": "received"}
    except Exception as e:
        logger.exception("Failed to process incoming WhatsApp message: %s", str(e))
        return {"status": "queued", "detail": str(e)}


async def reprocess_stored_whatsapp_messages():
    """Attempt to reprocess stored whatsapp messages left unprocessed from previous runs."""
    for msg in list(store.whatsapp_messages):
        if msg.get("processed"):
            continue
        try:
            mtype = msg.get("message_type")
            content = msg.get("content")
            phone = msg.get("phone")
            if mtype == "audio":
                store.create_task(customer_id=phone, service_type="help", description=content, urgency=1.25, base_price=150.0, distance_km=0.0, voice_note_url=content)
                msg["processed"] = True
            elif mtype == "text":
                v = VoiceProcessingService()
                await v.classify_voice_request(content)
                msg["processed"] = True
        except Exception:
            logger.exception("Reprocessing stored whatsapp message failed for id=%s", msg.get("id"))


@router.post("/send-message", dependencies=[Depends(require_role("admin"))])
async def send_whatsapp_message(phone_number: str, message: str):
    # only admins may send ad-hoc outbound messages
    clean = sanitize_text(message)
    store.store_whatsapp_message(phone=phone_number, direction="out", message_type="text", content=clean)
    ws = WhatsAppService()
    delivered = await ws.send_text_message(phone_number, clean)
    return {"status": "sent" if delivered else "queued"}


@router.post("/send-template-message", dependencies=[Depends(require_role("admin"))])
async def send_template_message(phone_number: str, template_type: str, data: dict):
    message = f"{template_type}: {data}"
    clean = sanitize_text(message)
    store.store_whatsapp_message(phone=phone_number, direction="out", message_type="template", content=clean)
    ws = WhatsAppService()
    delivered = await ws.send_text_message(phone_number, clean)
    return {"status": "sent" if delivered else "queued", "template_type": template_type}
