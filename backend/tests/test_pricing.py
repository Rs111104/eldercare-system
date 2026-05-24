"""
Pricing service tests
"""
import pytest


def test_calculate_price(client, auth_headers):
    """Test price calculation"""
    response = client.post(
        "/api/v1/pricing/calculate",
        json={
            "service_type": "medicine",
            "distance_km": 5,
            "urgency_level": 3,
            "effort_level": 2
        },
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_price" in data
    assert data["total_price"] > 0


def test_quick_mode_pricing(client, auth_headers):
    """Test quick mode pricing"""
    response = client.get(
        "/api/v1/pricing/quick-mode/medicine",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert "base_price" in response.json()


def test_scheduled_mode_pricing(client, auth_headers):
    """Test scheduled mode pricing"""
    response = client.get(
        "/api/v1/pricing/scheduled-mode/help",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert "base_price" in response.json()


def test_get_pricing_config(client, auth_headers):
    """Test getting pricing configuration"""
    response = client.get(
        "/api/v1/pricing/config/medicine",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 404]
