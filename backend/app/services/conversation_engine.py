from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from enum import Enum
from typing import cast

from app.core.redis_client import get_redis


class ConversationState(str, Enum):
    IDLE = "IDLE"
    GREETING = "GREETING"
    SERVICE_SELECT = "SERVICE_SELECT"
    DETAILS_COLLECT = "DETAILS_COLLECT"
    CONFIRM = "CONFIRM"
    AWAITING_WORKER = "AWAITING_WORKER"
    IN_PROGRESS = "IN_PROGRESS"
    FEEDBACK = "FEEDBACK"


@dataclass(frozen=True)
class ConversationResult:
    state: ConversationState
    reply: str
    language: str
    context: dict[str, str]


class ConversationEngine:
    TTL_SECONDS = 30 * 60
    SERVICES = {"1": "medicine", "2": "help", "3": "visit", "4": "cleaning"}
    SERVICE_NAMES = {"medicine", "help", "visit", "cleaning", "other"}
    MESSAGES = {
        "en": {
            "greeting": "Hello. I can help arrange elder care support. What service do you need?",
            "service_prompt": "Reply with 1 medicine, 2 home help, 3 visit, or 4 cleaning.",
            "details_prompt": "Please share the important details, including where and when help is needed.",
            "confirm_prompt": "I have the details. Reply yes to confirm or no to start again.",
            "confirmed": "Thank you. We are looking for a suitable worker and will keep you updated.",
            "invalid": "I did not understand that. Please try again.",
            "reset": "It has been a while, so I restarted this request. How can we help today?",
            "feedback": "Thank you. Your feedback has been recorded.",
        },
        "ta": {
            "greeting": "வணக்கம். மூத்தோர் பராமரிப்பு உதவியை ஏற்பாடு செய்யலாம். எந்த சேவை வேண்டும்?",
            "service_prompt": "1 மருந்து, 2 வீட்டு உதவி, 3 வருகை, 4 சுத்தம் என்று பதிலளிக்கவும்.",
            "details_prompt": "உதவி தேவைப்படும் இடம், நேரம் மற்றும் விவரங்களை பகிரவும்.",
            "confirm_prompt": "விவரங்கள் கிடைத்தன. உறுதிப்படுத்த yes அல்லது மீண்டும் தொடங்க no அனுப்பவும்.",
            "confirmed": "நன்றி. பொருத்தமான பணியாளரை தேடி உங்களுக்கு தகவல் தருகிறோம்.",
            "invalid": "அதை புரிந்துகொள்ள முடியவில்லை. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
            "reset": "சில நேரம் ஆகிவிட்டதால் கோரிக்கையை மீண்டும் தொடங்கினேன். இன்று எப்படி உதவலாம்?",
            "feedback": "நன்றி. உங்கள் கருத்து பதிவு செய்யப்பட்டது.",
        },
        "hi": {
            "greeting": "नमस्ते. मैं बुजुर्ग देखभाल सहायता की व्यवस्था कर सकता हूं. आपको कौन सी सेवा चाहिए?",
            "service_prompt": "1 दवा, 2 घर की मदद, 3 मुलाकात, या 4 सफाई लिखें.",
            "details_prompt": "कृपया जगह, समय और जरूरी विवरण साझा करें.",
            "confirm_prompt": "विवरण मिल गए हैं. पुष्टि के लिए yes या फिर से शुरू करने के लिए no लिखें.",
            "confirmed": "धन्यवाद. हम उपयुक्त कार्यकर्ता खोज रहे हैं और आपको अपडेट देंगे.",
            "invalid": "मैं समझ नहीं पाया. कृपया फिर से कोशिश करें.",
            "reset": "कुछ समय हो गया, इसलिए मैंने अनुरोध फिर से शुरू किया. आज कैसे मदद कर सकते हैं?",
            "feedback": "धन्यवाद. आपकी प्रतिक्रिया दर्ज कर ली गई है.",
        },
    }
    _memory: dict[str, dict[str, object]] = {}

    async def handle_message(self, phone: str, message: str, message_type: str = "text") -> ConversationResult:
        key = self._key(phone)
        record = self._load(key)
        language = str(record.get("language") or self._detect_language(message))
        state = ConversationState(str(record.get("state") or ConversationState.IDLE.value))
        raw_context = record.get("context") or {}
        context = dict(cast(dict[str, str], raw_context))

        if self._expired(record):
            state = ConversationState.IDLE
            context = {}
            reply_prefix = self._message(language, "reset") + " "
        else:
            reply_prefix = ""

        result = self._advance(state, language, context, message.strip(), message_type)
        self._save(key, result)
        if reply_prefix:
            return ConversationResult(result.state, reply_prefix + result.reply, result.language, result.context)
        return result

    def _advance(
        self,
        state: ConversationState,
        language: str,
        context: dict[str, str],
        message: str,
        message_type: str,
    ) -> ConversationResult:
        normalized = message.lower()
        if state in {ConversationState.IDLE, ConversationState.GREETING}:
            service = self._extract_service(normalized)
            if service:
                context["service_type"] = service
                return self._result(ConversationState.DETAILS_COLLECT, language, context, "details_prompt")
            return self._result(ConversationState.SERVICE_SELECT, language, context, "greeting", "service_prompt")

        if state == ConversationState.SERVICE_SELECT:
            service = self._extract_service(normalized)
            if not service:
                return self._result(state, language, context, "invalid", "service_prompt")
            context["service_type"] = service
            return self._result(ConversationState.DETAILS_COLLECT, language, context, "details_prompt")

        if state == ConversationState.DETAILS_COLLECT:
            if len(message) < 8:
                return self._result(state, language, context, "invalid", "details_prompt")
            context["details"] = message
            context["message_type"] = message_type
            return self._result(ConversationState.CONFIRM, language, context, "confirm_prompt")

        if state == ConversationState.CONFIRM:
            if normalized in {"yes", "y", "confirm", "ok", "okay"}:
                return self._result(ConversationState.AWAITING_WORKER, language, context, "confirmed")
            if normalized in {"no", "n", "cancel", "restart"}:
                return self._result(ConversationState.SERVICE_SELECT, language, {}, "service_prompt")
            return self._result(state, language, context, "invalid", "confirm_prompt")

        if state == ConversationState.FEEDBACK:
            context["feedback"] = message
            return self._result(ConversationState.IDLE, language, context, "feedback")

        return self._result(state, language, context, "confirmed")

    def _result(
        self,
        state: ConversationState,
        language: str,
        context: dict[str, str],
        *message_keys: str,
    ) -> ConversationResult:
        reply = " ".join(self._message(language, key) for key in message_keys)
        return ConversationResult(state=state, reply=reply, language=language, context=context)

    def _extract_service(self, normalized: str) -> str | None:
        if normalized in self.SERVICES:
            return self.SERVICES[normalized]
        for service in self.SERVICE_NAMES:
            if service in normalized:
                return service
        return None

    def _message(self, language: str, key: str) -> str:
        return self.MESSAGES.get(language, self.MESSAGES["en"])[key]

    def _detect_language(self, message: str) -> str:
        if any("\u0b80" <= char <= "\u0bff" for char in message):
            return "ta"
        if any("\u0900" <= char <= "\u097f" for char in message):
            return "hi"
        return "en"

    def _load(self, key: str) -> dict[str, object]:
        redis_client = get_redis()
        if redis_client:
            raw = redis_client.get(key)
            if raw:
                return cast(dict[str, object], json.loads(raw))
        return dict(self._memory.get(key) or {})

    def _save(self, key: str, result: ConversationResult) -> None:
        payload: dict[str, object] = {
            "state": result.state.value,
            "language": result.language,
            "context": result.context,
            "updated_at": time.time(),
        }
        redis_client = get_redis()
        if redis_client:
            redis_client.set(key, json.dumps(payload), ex=self.TTL_SECONDS)
            return
        self._memory[key] = payload

    def _expired(self, record: dict[str, object]) -> bool:
        raw_updated_at = record.get("updated_at") or time.time()
        updated_at = float(cast(float | str, raw_updated_at))
        return bool(record) and time.time() - updated_at > self.TTL_SECONDS

    def _key(self, phone: str) -> str:
        digest = hashlib.sha256(phone.encode("utf-8")).hexdigest()
        return f"conversation:{digest}"
