"""
Task endpoint tests
"""
import pytest


def test_create_task(client, auth_headers, sample_task):
    """Test task creation"""
    response = client.post(
        "/api/v1/tasks/create",
        json=sample_task,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == sample_task["title"]
    assert data["status"] == "created"


def test_get_task(client, auth_headers, sample_task):
    """Test getting task details"""
    # Create task first
    create_response = client.post(
        "/api/v1/tasks/create",
        json=sample_task,
        headers=auth_headers
    )
    task_id = create_response.json()["task_id"]
    
    # Get task
    response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["task_id"] == task_id


def test_cancel_task(client, auth_headers, sample_task):
    """Test task cancellation"""
    # Create task
    create_response = client.post(
        "/api/v1/tasks/create",
        json=sample_task,
        headers=auth_headers
    )
    task_id = create_response.json()["task_id"]
    
    # Cancel task
    response = client.post(
        f"/api/v1/tasks/{task_id}/cancel",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_get_customer_tasks(client, auth_headers):
    """Test getting customer's tasks"""
    response = client.get(
        "/api/v1/tasks/customer/test-customer-123",
        headers=auth_headers
    )
    
    assert response.status_code in [200, 404]


def test_update_task_status(client, auth_headers, sample_task):
    """Test updating task status"""
    # Create task
    create_response = client.post(
        "/api/v1/tasks/create",
        json=sample_task,
        headers=auth_headers
    )
    task_id = create_response.json()["task_id"]
    
    # Update status
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"status": "in_progress"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
