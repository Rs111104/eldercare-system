from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.matching_engine import MatchingEngine


def test_matching_engine_ranks_by_weighted_score():
    task = {"service_type": "medicine", "lat": 12.9, "lng": 77.6}
    workers = [
        {
            "id": "far-expert",
            "service_type": "medicine",
            "is_verified": True,
            "current_lat": 13.1,
            "current_lng": 77.8,
            "rating": 5.0,
            "completed_tasks": 100,
        },
        {
            "id": "near-good",
            "service_type": "medicine",
            "is_verified": True,
            "current_lat": 12.901,
            "current_lng": 77.601,
            "rating": 4.5,
            "completed_tasks": 20,
        },
    ]

    matches = MatchingEngine().rank_workers(task=task, workers=workers)

    assert [match.worker["id"] for match in matches] == ["near-good", "far-expert"]
    assert matches[0].factors["distance_score"] > matches[1].factors["distance_score"]


def test_matching_engine_filters_unavailable_and_low_score_workers():
    task = {"service_type": "help", "lat": 0.0, "lng": 0.0}
    workers = [
        {
            "id": "too-far",
            "service_type": "help",
            "is_verified": True,
            "current_lat": 5.0,
            "current_lng": 5.0,
            "rating": 1.0,
        },
        {
            "id": "wrong-service",
            "service_type": "medicine",
            "is_verified": True,
            "current_lat": 0.0,
            "current_lng": 0.0,
            "rating": 5.0,
        },
    ]

    assert MatchingEngine().rank_workers(task=task, workers=workers) == []


def test_matching_engine_scores_availability_overlap():
    start = datetime.now(timezone.utc).replace(microsecond=0)
    end = start + timedelta(hours=2)
    task = {
        "service_type": "visit",
        "lat": 10.0,
        "lng": 10.0,
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
    }
    worker = {
        "id": "partial",
        "service_type": "visit",
        "is_verified": True,
        "current_lat": 10.0,
        "current_lng": 10.0,
        "rating": 5.0,
        "availability_windows": [{"start": start.isoformat(), "end": (start + timedelta(hours=1)).isoformat()}],
    }

    match = MatchingEngine().rank_workers(task=task, workers=[worker])[0]

    assert match.factors["availability_score"] == 0.5
