"""
Voice processing service - convert audio to text and classify tasks
"""
import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core import metrics
from app.core.retry import retry_async

logger = logging.getLogger(__name__)

class VoiceProcessingService:
    def __init__(self):
        self.openai_api_key = settings.OPENAI_API_KEY

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> Optional[str]:
        """Convert voice note to text using OpenAI Whisper"""
        
        try:
            import openai
            openai.api_key = self.openai_api_key

            # Create a temporary file-like object
            import io
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "voice_note.m4a"

            @retry_async(retries=3)
            async def _transcribe(file_obj):
                # openai SDK does blocking IO; call in thread if needed
                return openai.Audio.transcribe(model="whisper-1", file=file_obj, language=language)

            started = time.perf_counter()
            transcript = await asyncio.wait_for(_transcribe(audio_file), timeout=settings.OPENAI_TIMEOUT_SECONDS)
            self._observe_openai(started, "transcribe", {"input_bytes": len(audio_bytes), "output_chars": len(transcript.get("text", ""))})
            return transcript.get("text", "")

        except Exception as e:
            logger.exception("openai_transcription_failed", extra={"action": "openai.transcribe", "status": "failed"})
            return "Voice note received. Please review the original audio if details are unclear."

    async def classify_voice_request(self, text: str) -> Dict[str, Any]:
        """Classify voice request using GPT to extract task details"""
        
        try:
            import openai
            openai.api_key = self.openai_api_key
            
            # Prompt for classification
            prompt = f"""
            Analyze the following voice note from an elderly person requesting a service.
            Extract and return as JSON:
            - task_type: one of [medicine, help, visit, cleaning, other]
            - title: brief task title (max 50 chars)
            - description: detailed description
            - urgency_level: 1-5 (1=normal, 5=emergency)
            - estimated_effort: 1-5 (1=simple, 5=complex)
            
            Voice note: "{text}"
            
            Return only valid JSON without markdown formatting.
            """
            
            @retry_async(retries=3)
            async def _chat_create(payload):
                return openai.ChatCompletion.create(**payload)

            started = time.perf_counter()
            response = await asyncio.wait_for(_chat_create({
                "model": "gpt-4",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 200,
            }), timeout=settings.OPENAI_TIMEOUT_SECONDS)
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            result = json.loads(response_text)
            usage = getattr(response, "usage", None)
            self._observe_openai(started, "classify", {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
            })
            
            # Validate fields
            valid_types = ["medicine", "help", "visit", "cleaning", "other"]
            if result.get("task_type") not in valid_types:
                result["task_type"] = "other"
            
            result["urgency_level"] = max(1, min(5, result.get("urgency_level", 2)))
            result["estimated_effort"] = max(1, min(5, result.get("estimated_effort", 2)))
            
            return result
        
        except json.JSONDecodeError:
            logger.exception("openai_classification_parse_failed", extra={"action": "openai.classify", "status": "fallback"})
            return {
                "task_type": "other",
                "title": "Service Request",
                "description": text,
                "urgency_level": 2,
                "estimated_effort": 2
            }
        except Exception as e:
            logger.exception("openai_classification_failed", extra={"action": "openai.classify", "status": "fallback"})
            return {
                "task_type": "other",
                "title": "Service Request",
                "description": text,
                "urgency_level": 2,
                "estimated_effort": 2
            }

    def _observe_openai(self, started: float, action: str, usage: Dict[str, Any]) -> None:
        elapsed = time.perf_counter() - started
        logger.info("openai_call", extra={"action": f"openai.{action}", "status": "success", "duration_ms": int(elapsed * 1000), "token_usage": usage})
        try:
            if metrics.OPENAI_CALL_DURATION is not None:
                metrics.OPENAI_CALL_DURATION.observe(elapsed)
        except Exception:
            pass

    async def extract_location_from_text(self, text: str) -> Optional[Dict[str, float]]:
        """Extract location information from text"""
        
        # This would use a location extraction API or service
        # For now, returning None as location needs GPS/address input
        return None

    async def generate_task_summary(self, task_details: Dict[str, Any]) -> str:
        """Generate a summary of the task for the customer"""
        
        summary = f"""
        Task Summary:
        - Type: {task_details.get('task_type')}
        - Title: {task_details.get('title')}
        - Urgency: {task_details.get('urgency_level')}/5
        - Estimated Effort: {task_details.get('estimated_effort')}/5
        
        Description: {task_details.get('description')}
        """
        
        return summary.strip()
