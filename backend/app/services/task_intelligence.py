from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskEstimate:
    duration_minutes: int
    estimated_price: float
    suggest_weekly: bool


class TaskIntelligenceService:
    DEFAULT_DURATIONS = {"medicine": 45, "help": 90, "visit": 60, "cleaning": 120, "other": 60}

    def estimate(self, store, customer_id: str, service_type: str, distance_km: float, urgency: float) -> TaskEstimate:
        pricing = store.calculate_pricing_breakdown(service_type, distance_km, urgency, customer_id=customer_id)
        previous = [
            task
            for task in store.tasks.values()
            if task.get("customer_id") == customer_id and task.get("service_type") == service_type
        ]
        return TaskEstimate(
            duration_minutes=self.duration_for_service(store, service_type),
            estimated_price=float(pricing["total_price"]),
            suggest_weekly=len(previous) >= 3,
        )

    def duration_for_service(self, store, service_type: str) -> int:
        settings = getattr(store, "runtime_settings", {})
        durations = settings.get("service_durations_minutes", {}) if isinstance(settings, dict) else {}
        return int(durations.get(service_type, self.DEFAULT_DURATIONS.get(service_type, self.DEFAULT_DURATIONS["other"])))
