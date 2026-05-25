"""
Test fixtures and utilities
"""
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.core.config import settings
from app.store import store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Create authentication headers for testing"""
    # Register user
    response = client.post(
        f"{settings.API_V1_STR}/auth/register/customer",
        json={
            "phone_number": "+919876543210",
            "password": "TestPassword123!"
        }
    )
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_task():
    """Sample task data"""
    return {
        "title": "Medicine Delivery",
        "description": "Deliver prescribed medicines to elder patient",
        "task_type": "medicine",
        "mode": "quick",
        "urgency_level": 3,
        "location": "123 Main St, City, State 12345",
    }


@pytest.fixture
def sample_worker():
    """Sample worker data"""
    return {
        "phone_number": "+919876543210",
        "service_types": ["medicine", "help"],
        "location_lat": 28.7041,
        "location_lng": 77.1025
    }


@pytest.fixture
def sample_pricing_config():
    """Sample pricing configuration"""
    return {
        "service_type": "medicine",
        "base_price": 50,
        "distance_charge_per_km": 5,
        "effort_multiplier": 1.0
    }
