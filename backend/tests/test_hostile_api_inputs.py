from __future__ import annotations

from datetime import timedelta

from jose import jwt

from app.config import settings
from app.core.security import create_access_token
from app.store import store


def test_empty_post_body_returns_safe_validation_error(client):
    response = client.post("/api/v1/auth/register/customer", content=b"")

    assert response.status_code == 422
    assert response.json() == {
        "error": True,
        "code": "VALIDATION_ERROR",
        "message": "Please check the request and try again.",
        "timestamp": response.json()["timestamp"],
    }
    assert "phone_number" not in response.text


def test_unknown_fields_do_not_leak_schema_details(client):
    response = client.post(
        "/api/v1/auth/register/customer",
        json={"phone_number": "+919999999999", "password": "TestPassword123!", "is_super_admin": True},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "is_super_admin" not in response.text


def test_oversized_and_negative_task_input_is_rejected(client, auth_headers):
    response = client.post(
        "/api/v1/tasks/create",
        json={"title": "x" * 200, "description": "x" * 2500, "task_type": "medicine", "urgency": -1},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert response.json()["message"] == "Please check the request and try again."


def test_protected_endpoint_without_token_is_safe(client):
    response = client.get("/api/v1/tasks/available/quick")

    assert response.status_code == 401
    assert response.json()["error"] is True
    assert "traceback" not in response.text.lower()


def test_tampered_wrong_secret_and_expired_tokens_are_rejected(client):
    expired = create_access_token("user-1", "+910000000000", "admin", expires_delta=timedelta(seconds=-1))
    wrong_secret = jwt.encode(
        {"user_id": "user-1", "phone_number": "+910000000000", "user_type": "admin"},
        "wrong-secret",
        algorithm=settings.ALGORITHM,
    )

    for token in (expired, wrong_secret):
        response = client.get("/api/v1/admin/stats/overview", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["message"] == "Invalid or expired token"


def test_customer_cannot_reach_admin_endpoint(client, auth_headers):
    response = client.get("/api/v1/admin/stats/overview", headers=auth_headers)

    assert response.status_code == 403
    assert response.json()["message"] == "Forbidden: insufficient role"


def test_replayed_task_create_has_separate_explicit_tasks(client, auth_headers):
    customer_id = store.list_customers()[0]["id"]
    payload = {"customer_id": customer_id, "title": "Medicine", "description": "Bring tablets", "task_type": "medicine"}

    first = client.post("/api/v1/tasks/create", json=payload, headers=auth_headers)
    second = client.post("/api/v1/tasks/create", json=payload, headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["task_id"] != second.json()["task_id"]
