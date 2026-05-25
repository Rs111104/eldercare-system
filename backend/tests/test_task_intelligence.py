from __future__ import annotations

from app.services.task_intelligence import TaskIntelligenceService
from app.store import store


def test_task_intelligence_estimates_price_duration_and_recurring_suggestion():
    customer = store.create_customer("+1000000010", "Customer")
    for index in range(3):
        store.create_task(customer["id"], "medicine", f"Medicine {index}", 1.0, 120.0, 0.0)

    estimate = TaskIntelligenceService().estimate(store, customer["id"], "medicine", 0.0, 1.0)

    assert estimate.duration_minutes == 45
    assert estimate.estimated_price > 0
    assert estimate.suggest_weekly is True


def test_task_intelligence_uses_runtime_duration_settings():
    store.runtime_settings["service_durations_minutes"] = {"cleaning": 150}

    assert TaskIntelligenceService().duration_for_service(store, "cleaning") == 150
