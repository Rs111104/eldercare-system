"""
Authentication endpoint tests
"""

from app.core.config import settings


def test_customer_registration(client):
    """Test customer registration"""
    response = client.post(
        "/api/v1/auth/register/customer",
        json={
            "phone_number": "+919876543210",
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_type"] == "customer"


def test_worker_registration(client):
    """Test worker registration"""
    response = client.post(
        "/api/v1/auth/register/worker",
        json={
            "phone_number": "+918765432109",
            "password": "TestPassword123!",
            "service_types": ["medicine", "help"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user_type"] == "worker"


def test_login(client):
    """Test user login"""
    # First register
    client.post(
        "/api/v1/auth/register/customer",
        json={
            "phone_number": "+919876543210",
            "password": "TestPassword123!"
        }
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "+919876543210",
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "phone_number": "+919876543210",
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401


def test_admin_registration_requires_bootstrap_token_when_no_admins(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_BOOTSTRAP_TOKEN", "bootstrap-secret")

    response = client.post(
        "/api/v1/auth/register/admin",
        json={
            "phone_number": "+910000000001",
            "password": "AdminPassword123!",
        },
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
    )

    assert response.status_code == 200
    assert response.json()["user_type"] == "admin"


def test_admin_registration_requires_admin_after_bootstrap(client, monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_BOOTSTRAP_TOKEN", "bootstrap-secret")

    bootstrap_response = client.post(
        "/api/v1/auth/register/admin",
        json={
            "phone_number": "+910000000002",
            "password": "AdminPassword123!",
        },
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
    )
    assert bootstrap_response.status_code == 200
    admin_token = bootstrap_response.json()["access_token"]

    forbidden_response = client.post(
        "/api/v1/auth/register/admin",
        json={
            "phone_number": "+910000000003",
            "password": "AdminPassword123!",
        },
    )
    assert forbidden_response.status_code == 403

    allowed_response = client.post(
        "/api/v1/auth/register/admin",
        json={
            "phone_number": "+910000000004",
            "password": "AdminPassword123!",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed_response.status_code == 200
