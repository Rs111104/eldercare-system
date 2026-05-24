from __future__ import annotations

from app.store import store


class AIService:
    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        return f"transcribed {len(audio_bytes)} bytes"

    async def classify_text(self, text: str) -> dict:
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["medicine", "pill", "tablet"]):
            task_type = "medicine"
        elif any(keyword in text_lower for keyword in ["clean", "sweep", "wash"]):
            task_type = "cleaning"
        else:
            task_type = "help"
        return {"task_type": task_type, "urgency_level": 2, "location": None, "description": text}

    async def classify_voice_request(self, text: str) -> dict:
        return await self.classify_text(text)
