from __future__ import annotations

from app.services.worker_conversation import WorkerConversationService
from app.store import store


def test_worker_conversation_sets_unavailability():
    worker = store.create_worker("+1000000020", "Worker", "help", is_verified=True)

    result = WorkerConversationService().handle_message(store, worker["id"], "Unavailable 2026-12-25")

    assert result.action == "unavailable"
    assert store.workers[worker["id"]]["unavailable_dates"] == ["2026-12-25"]


def test_worker_conversation_returns_earnings_breakdown():
    service = WorkerConversationService()
    task = {"title": "Grocery shopping", "price": 450}
    payout = {"gross_amount": 450, "platform_fee": 50, "net_amount": 400}

    message = service.earnings_breakdown(task, payout, "xxxx1234")

    assert "Grocery shopping" in message
    assert "Your payout: Rs 400.00" in message
