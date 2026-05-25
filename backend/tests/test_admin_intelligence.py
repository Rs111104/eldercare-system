from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.admin_intelligence import AdminIntelligenceService
from app.store import store


def test_admin_intelligence_flags_fast_completion():
    customer = store.create_customer("+1000000000", "Customer")
    worker = store.create_worker("+1000000001", "Worker", "help", is_verified=True)
    task = store.create_task(customer["id"], "help", "Help needed", 1.0, 100.0, 0.0, worker_id=worker["id"])
    start = datetime.now(timezone.utc) - timedelta(minutes=5)
    store.tasks[task["id"]]["created_at"] = start.isoformat()
    store.tasks[task["id"]]["completed_at"] = datetime.now(timezone.utc).isoformat()
    store.tasks[task["id"]]["estimated_duration_minutes"] = 90

    anomalies = AdminIntelligenceService().detect_anomalies(store)

    assert any(anomaly.rule == "fast_completion" for anomaly in anomalies)


def test_admin_intelligence_flags_frequent_customer_disputes():
    customer = store.create_customer("+1000000002", "Customer")
    worker = store.create_worker("+1000000003", "Worker", "help", is_verified=True)
    for index in range(3):
        task = store.create_task(customer["id"], "help", f"Task {index}", 1.0, 100.0, 0.0, worker_id=worker["id"])
        store.tasks[task["id"]]["lifecycle_status"] = "COMPLETED"
        store.add_review(task["id"], customer["id"], worker["id"], 1, "bad")

    anomalies = AdminIntelligenceService().detect_anomalies(store)

    assert any(anomaly.rule == "frequent_customer_disputes" for anomaly in anomalies)


def test_weekly_digest_reports_business_health():
    customer = store.create_customer("+1000000004", "Customer")
    worker = store.create_worker("+1000000005", "Worker", "medicine", is_verified=True)
    task = store.create_task(customer["id"], "medicine", "Medicine", 1.0, 120.0, 0.0, worker_id=worker["id"])
    store.tasks[task["id"]]["status"] = "completed"
    store.tasks[task["id"]]["completed_at"] = datetime.now(timezone.utc).isoformat()
    store.workers[worker["id"]]["completed_tasks"] = 4

    digest = AdminIntelligenceService().weekly_digest(store)

    assert digest["tasks_completed"] == 1
    assert digest["revenue"] > 0
    assert digest["top_workers"][0]["worker_id"] == worker["id"]
