from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class Anomaly:
    rule: str
    record_type: str
    record_id: str
    reason: str
    severity: str = "medium"


class AdminIntelligenceService:
    def detect_anomalies(self, store) -> list[Anomaly]:
        anomalies: list[Anomaly] = []
        anomalies.extend(self._fast_completion_anomalies(store))
        anomalies.extend(self._customer_dispute_anomalies(store))
        anomalies.extend(self._worker_rating_drop_anomalies(store))
        anomalies.extend(self._payout_amount_anomalies(store))
        return anomalies

    def flag_anomalies(self, store) -> list[dict]:
        flagged = []
        for anomaly in self.detect_anomalies(store):
            if self._already_flagged(store, anomaly):
                continue
            flagged.append(store._flag_item(anomaly.record_type, anomaly.record_id, anomaly.reason))
        return flagged

    def weekly_digest(self, store, days: int = 7) -> dict:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        tasks = [task for task in store.tasks.values() if self._created_since(task, since)]
        completed = [task for task in tasks if task.get("status") == "completed"]
        revenue = round(sum(float(task.get("price", 0.0)) for task in completed), 2)
        unmatched = [item for item in getattr(store, "matching_decisions", []) if item.get("candidate_count") == 0]
        return {
            "period_days": days,
            "tasks_completed": len(completed),
            "revenue": revenue,
            "top_workers": self._top_workers(store),
            "top_issues": self._top_issues(store),
            "unmatched_task_rate": round(len(unmatched) / max(len(tasks), 1), 4),
        }

    def _fast_completion_anomalies(self, store) -> list[Anomaly]:
        anomalies = []
        for task in store.tasks.values():
            estimated = float(task.get("estimated_duration_minutes") or self._estimated_duration(task))
            elapsed = self._elapsed_minutes(task.get("created_at"), task.get("completed_at"))
            if elapsed is not None and estimated > 0 and elapsed < estimated * 0.2:
                anomalies.append(Anomaly("fast_completion", "task", task["id"], "Task completed unusually quickly", "high"))
        return anomalies

    def _customer_dispute_anomalies(self, store) -> list[Anomaly]:
        since = datetime.now(timezone.utc) - timedelta(days=30)
        disputes: dict[str, int] = {}
        for review in store.reviews.values():
            if review.get("is_disputed") and self._created_since(review, since):
                customer_id = str(review.get("customer_id", ""))
                disputes[customer_id] = disputes.get(customer_id, 0) + 1
        return [
            Anomaly("frequent_customer_disputes", "customer", customer_id, "Customer disputed more than two tasks in 30 days", "high")
            for customer_id, count in disputes.items()
            if count > 2
        ]

    def _worker_rating_drop_anomalies(self, store) -> list[Anomaly]:
        anomalies = []
        for worker in store.workers.values():
            previous = worker.get("rating_7d_ago")
            current = worker.get("rating")
            if previous is not None and current is not None and float(previous) - float(current) > 1.0:
                anomalies.append(Anomaly("rating_drop", "worker", worker["id"], "Worker rating dropped by more than 1 point in 7 days"))
        return anomalies

    def _payout_amount_anomalies(self, store) -> list[Anomaly]:
        by_worker: dict[str, list[float]] = {}
        for payout in store.payouts.values():
            by_worker.setdefault(str(payout.get("worker_id")), []).append(float(payout.get("amount", 0.0)))
        anomalies = []
        for payout in store.payouts.values():
            amounts = [amount for amount in by_worker.get(str(payout.get("worker_id")), []) if amount > 0]
            average = sum(amounts) / len(amounts) if amounts else 0.0
            if average > 0 and float(payout.get("amount", 0.0)) > average * 3:
                anomalies.append(Anomaly("large_payout", "payout", payout["id"], "Payout is more than 3x worker average payout"))
        return anomalies

    def _top_workers(self, store) -> list[dict]:
        workers = sorted(store.workers.values(), key=lambda worker: int(worker.get("completed_tasks", 0)), reverse=True)
        return [{"worker_id": worker["id"], "completed_tasks": int(worker.get("completed_tasks", 0))} for worker in workers[:5]]

    def _top_issues(self, store) -> list[dict]:
        issues: dict[str, int] = {}
        for item in getattr(store, "flagged_items", []):
            reason = str(item.get("reason", "unknown"))
            issues[reason] = issues.get(reason, 0) + 1
        return [{"reason": reason, "count": count} for reason, count in sorted(issues.items(), key=lambda item: -item[1])[:5]]

    def _already_flagged(self, store, anomaly: Anomaly) -> bool:
        return any(
            item.get("record_type") == anomaly.record_type
            and item.get("record_id") == anomaly.record_id
            and item.get("reason") == anomaly.reason
            for item in getattr(store, "flagged_items", [])
        )

    def _estimated_duration(self, task: dict) -> float:
        defaults = {"medicine": 45.0, "help": 90.0, "visit": 60.0, "cleaning": 120.0}
        return defaults.get(str(task.get("service_type")), 60.0)

    def _elapsed_minutes(self, start: object, end: object) -> float | None:
        start_dt = self._parse_time(start)
        end_dt = self._parse_time(end)
        if start_dt is None or end_dt is None:
            return None
        return max(0.0, (end_dt - start_dt).total_seconds() / 60.0)

    def _created_since(self, record: dict, since: datetime) -> bool:
        created_at = self._parse_time(record.get("created_at"))
        return created_at is not None and created_at >= since

    def _parse_time(self, value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
