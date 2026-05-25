from __future__ import annotations

import time
import asyncio

import pytest

from app.services.conversation_engine import ConversationEngine, ConversationState


@pytest.fixture(autouse=True)
def clear_conversation_memory():
    ConversationEngine._memory.clear()
    yield
    ConversationEngine._memory.clear()


def run(coro):
    return asyncio.run(coro)


def test_conversation_collects_service_details_and_confirmation():
    engine = ConversationEngine()

    first = run(engine.handle_message("+1000000000", "medicine"))
    second = run(engine.handle_message("+1000000000", "Please deliver blood pressure tablets tomorrow morning"))
    third = run(engine.handle_message("+1000000000", "yes"))

    assert first.state == ConversationState.DETAILS_COLLECT
    assert second.state == ConversationState.CONFIRM
    assert third.state == ConversationState.AWAITING_WORKER
    assert third.context["service_type"] == "medicine"


def test_conversation_reprompts_on_invalid_service():
    result = run(ConversationEngine().handle_message("+1000000001", "something unclear"))

    assert result.state == ConversationState.SERVICE_SELECT
    assert "medicine" in result.reply


def test_conversation_detects_tamil():
    result = run(ConversationEngine().handle_message("+1000000002", "மருந்து உதவி வேண்டும்"))

    assert result.language == "ta"
    assert result.state == ConversationState.SERVICE_SELECT


def test_conversation_resets_after_ttl():
    engine = ConversationEngine()
    run(engine.handle_message("+1000000003", "1"))
    key = engine._key("+1000000003")
    ConversationEngine._memory[key]["updated_at"] = time.time() - engine.TTL_SECONDS - 1

    result = run(engine.handle_message("+1000000003", "yes"))

    assert result.state == ConversationState.SERVICE_SELECT
    assert "restarted" in result.reply
