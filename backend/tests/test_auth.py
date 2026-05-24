"""
Authentication endpoint tests
"""
import pytest


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
