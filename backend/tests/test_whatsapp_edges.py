from __future__ import annotations

import hashlib
import hmac
import json

import pytest

from app.config import settings
from app.store import store


def signed_body(payload: dict) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(payload).encode("utf-8")
    signature = hmac.new(settings.WHATSAPP_APP_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return body, {"X-Hub-Signature-256": f"sha256={signature}", "Content-Type": "application/json"}


@pytest.fixture(autouse=True)
def whatsapp_secret(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", "test-secret")


def post_webhook(client, payload: dict):
    body, headers = signed_body(payload)
    return client.post("/api/v1/whatsapp/webhook", content=body, headers=headers)


def test_whatsapp_blank_emoji_and_long_messages_do_not_crash(client, monkeypatch):
    async def classify(_self, text: str):
        return {"task_type": "other", "description": text, "urgency_level": 1}

    monkeypatch.setattr("app.services.voice_service.VoiceProcessingService.classify_voice_request", classify)

    for content in ("", "🙂🙂", "x" * 4000):
        response = post_webhook(client, {"phone": "+919999999999", "message_type": "text", "content": content})
        assert response.status_code == 200
        assert response.json()["status"] == "received"


def test_whatsapp_voice_note_degrades_to_transcribed_text(client, monkeypatch):
    async def download(_self, media_id: str, media_type: str = "audio"):
        return b"fake-audio"

    async def transcribe(_self, audio_bytes: bytes, language: str = "en"):
        return "Need help with medicine"

    async def classify(_self, text: str):
        return {"task_type": "medicine", "description": text, "urgency_level": 2}

    monkeypatch.setattr("app.services.whatsapp_service.WhatsAppService.download_media", download)
    monkeypatch.setattr("app.services.voice_service.VoiceProcessingService.transcribe_audio", transcribe)
    monkeypatch.setattr("app.services.voice_service.VoiceProcessingService.classify_voice_request", classify)

    response = post_webhook(client, {"phone": "+919999999991", "message_type": "audio", "content": "media-id"})

    assert response.status_code == 200
    assert response.json()["classification"]["task_type"] == "medicine"
    inbound = [item for item in store.whatsapp_messages if item["direction"] == "in"][-1]
    assert inbound["transcription"] == "Need help with medicine"


def test_whatsapp_duplicate_delivery_is_idempotent(client, monkeypatch):
    async def classify(_self, text: str):
        return {"task_type": "other", "description": text, "urgency_level": 1}

    monkeypatch.setattr("app.services.voice_service.VoiceProcessingService.classify_voice_request", classify)
    payload = {"phone": "+919999999992", "message_type": "text", "content": "Need help"}

    first = post_webhook(client, payload)
    second = post_webhook(client, payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True


def test_whatsapp_missing_required_field_and_bad_signature_are_safe(client):
    bad_body = json.dumps({"message_type": "text", "content": "hello"}).encode("utf-8")
    bad_signature = client.post(
        "/api/v1/whatsapp/webhook",
        content=bad_body,
        headers={"X-Hub-Signature-256": "sha256=bad", "Content-Type": "application/json"},
    )
    assert bad_signature.status_code == 403

    body, headers = signed_body({"message_type": "text", "content": "hello"})
    missing_field = client.post("/api/v1/whatsapp/webhook", content=body, headers=headers)
    assert missing_field.status_code == 422
    assert missing_field.json()["code"] == "VALIDATION_ERROR"
