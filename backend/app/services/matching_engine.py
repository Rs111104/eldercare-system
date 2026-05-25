from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from app.utils.geo import haversine


@dataclass(frozen=True)
class MatchScore:
    worker: dict
    distance_km: float
    score: float
    factors: dict[str, float]


class MatchingEngine:
    MINIMUM_SCORE = 0.4
    WEIGHTS = {
        "distance": 0.35,
        "rating": 0.30,
        "availability": 0.20,
        "experience": 0.15,
    }

    def rank_workers(
        self,
        *,
        task: Mapping[str, object],
        workers: Sequence[Mapping[str, object]],
        max_radius_km: float = 40.0,
        limit: int = 5,
    ) -> list[MatchScore]:
        scored = [
            score
            for worker in workers
            if (score := self._score_worker(task, worker, max_radius_km)) is not None
        ]
        scored.sort(key=lambda item: (-item.score, item.distance_km, -item.factors["rating_score"]))
        selected = scored[:limit]
        if selected and selected[0].score >= self.MINIMUM_SCORE:
            return selected
        return []

    def _score_worker(
        self,
        task: Mapping[str, object],
        worker: Mapping[str, object],
        max_radius_km: float,
    ) -> MatchScore | None:
        if not worker.get("is_verified") or worker.get("is_frozen"):
            return None
        service_type = str(task.get("service_type") or task.get("task_type") or "")
        if not self._can_perform(worker, service_type):
            return None

        distance = self._distance_km(task, worker)
        if distance is None or distance > max_radius_km:
            return None

        factors = {
            "distance_score": max(0.0, 1.0 - (distance / max_radius_km)),
            "rating_score": self._rating_score(worker),
            "availability_score": self._availability_score(task, worker),
            "experience_score": self._experience_score(worker, service_type),
        }
        score = round(
            (factors["distance_score"] * self.WEIGHTS["distance"])
            + (factors["rating_score"] * self.WEIGHTS["rating"])
            + (factors["availability_score"] * self.WEIGHTS["availability"])
            + (factors["experience_score"] * self.WEIGHTS["experience"]),
            4,
        )
        return MatchScore(worker=dict(worker), distance_km=round(distance, 2), score=score, factors=factors)

    def _distance_km(self, task: Mapping[str, object], worker: Mapping[str, object]) -> float | None:
        task_lat = task.get("lat", task.get("location_lat"))
        task_lng = task.get("lng", task.get("location_lng"))
        worker_lat = worker.get("current_lat", worker.get("location_lat"))
        worker_lng = worker.get("current_lng", worker.get("location_lng"))
        if None in {task_lat, task_lng, worker_lat, worker_lng}:
            return None
        return haversine(self._as_float(task_lat), self._as_float(task_lng), self._as_float(worker_lat), self._as_float(worker_lng))

    def _can_perform(self, worker: Mapping[str, object], service_type: str) -> bool:
        service_types = worker.get("service_types")
        if isinstance(service_types, list):
            return service_type in {str(item) for item in service_types}
        return str(worker.get("service_type") or "") == service_type

    def _rating_score(self, worker: Mapping[str, object]) -> float:
        return max(0.0, min(self._as_float(worker.get("rating") or worker.get("avg_rating") or 5.0) / 5.0, 1.0))

    def _experience_score(self, worker: Mapping[str, object], service_type: str) -> float:
        completed_by_service = worker.get("completed_by_service")
        if isinstance(completed_by_service, dict):
            completed = completed_by_service.get(service_type, 0)
        else:
            completed = worker.get("completed_tasks", 0)
        return max(0.0, min(self._as_float(completed or 0) / 100.0, 1.0))

    def _availability_score(self, task: Mapping[str, object], worker: Mapping[str, object]) -> float:
        windows = worker.get("availability_windows")
        if not isinstance(windows, list) or not windows:
            return 1.0
        requested_start = self._parse_time(task.get("scheduled_start"))
        requested_end = self._parse_time(task.get("scheduled_end"))
        if requested_start is None or requested_end is None or requested_end <= requested_start:
            return 1.0
        requested_hours = (requested_end - requested_start).total_seconds() / 3600.0
        overlap_hours = sum(self._overlap_hours(requested_start, requested_end, window) for window in windows)
        return max(0.0, min(overlap_hours / requested_hours, 1.0))

    def _overlap_hours(self, requested_start: datetime, requested_end: datetime, window: object) -> float:
        if not isinstance(window, dict):
            return 0.0
        window_start = self._parse_time(window.get("start"))
        window_end = self._parse_time(window.get("end"))
        if window_start is None or window_end is None:
            return 0.0
        overlap = min(requested_end, window_end) - max(requested_start, window_start)
        return max(0.0, overlap.total_seconds() / 3600.0)

    def _parse_time(self, value: object) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _as_float(self, value: object) -> float:
        if isinstance(value, (int, float, str)):
            return float(value)
        raise TypeError("Expected numeric value")
