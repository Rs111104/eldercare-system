"""
Worker integration tests
"""
import pytest
from tests.test_utils import APITestBase, TestDataFactory, TestHelper


class TestWorkerIntegration(APITestBase):
    """Test worker-related endpoints and functionality"""
    
    def test_worker_registration(self):
        """Test worker can register"""
        response = self.helper.register_worker(self.client)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == "worker"
        assert "access_token" in data
    
    def test_worker_profile_fetch(self):
        """Test fetching worker profile"""
        # Register worker
        reg_response = self.helper.register_worker(self.client)
        token = reg_response.json()["access_token"]
        headers = self.helper.get_headers(token)
        worker_id = reg_response.json()["user_id"]
        
        # Fetch profile
        response = self.client.get(
            f"/api/v1/workers/{worker_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["worker_id"] == worker_id
    
    def test_worker_location_update(self):
        """Test worker location update"""
        # Register and login
        reg_response = self.helper.register_worker(self.client)
        token = reg_response.json()["access_token"]
        headers = self.helper.get_headers(token)
        worker_id = reg_response.json()["user_id"]
        
        # Update location
        response = self.client.put(
            f"/api/v1/workers/{worker_id}/location",
            json={
                "latitude": 28.7041,
                "longitude": 77.1025
            },
            headers=headers
        )
        
        assert response.status_code == 200
    
    def test_get_available_tasks(self):
        """Test worker can view available tasks"""
        # Register worker
        reg_response = self.helper.register_worker(self.client)
        token = reg_response.json()["access_token"]
        headers = self.helper.get_headers(token)
        worker_id = reg_response.json()["user_id"]
        
        # Get available tasks
        response = self.client.get(
            f"/api/v1/workers/{worker_id}/available-tasks",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_accept_task(self):
        """Test worker accepting a task"""
        # Register worker and customer
        worker_reg = self.helper.register_worker(self.client)
        worker_token = worker_reg.json()["access_token"]
        worker_id = worker_reg.json()["user_id"]
        worker_headers = self.helper.get_headers(worker_token)
        
        customer_reg = self.helper.register_customer(self.client)
        customer_token = customer_reg.json()["access_token"]
        customer_headers = self.helper.get_headers(customer_token)
        
        # Customer creates task
        task_response = self.helper.create_task(self.client, customer_headers)
        assert task_response.status_code == 200
        task_id = task_response.json()["task_id"]
        
        # Worker accepts task
        response = self.client.post(
            f"/api/v1/workers/{worker_id}/accept-task/{task_id}",
            headers=worker_headers
        )
        
        assert response.status_code == 200
    
    def test_worker_check_in(self):
        """Test worker checking in with proof"""
        # Setup
        worker_reg = self.helper.register_worker(self.client)
        worker_token = worker_reg.json()["access_token"]
        worker_id = worker_reg.json()["user_id"]
        worker_headers = self.helper.get_headers(worker_token)
        
        customer_reg = self.helper.register_customer(self.client)
        customer_token = customer_reg.json()["access_token"]
        customer_headers = self.helper.get_headers(customer_token)
        
        # Create and accept task
        task_response = self.helper.create_task(self.client, customer_headers)
        task_id = task_response.json()["task_id"]
        
        self.client.post(
            f"/api/v1/workers/{worker_id}/accept-task/{task_id}",
            headers=worker_headers
        )
        
        # Worker checks in
        response = self.client.post(
            f"/api/v1/workers/{worker_id}/check-in/{task_id}",
            json={"proof_photo_url": "https://example.com/photo.jpg"},
            headers=worker_headers
        )
        
        assert response.status_code == 200
    
    def test_worker_check_out(self):
        """Test worker checking out and completing task"""
        # Full setup
        worker_reg = self.helper.register_worker(self.client)
        worker_token = worker_reg.json()["access_token"]
        worker_id = worker_reg.json()["user_id"]
        worker_headers = self.helper.get_headers(worker_token)
        
        customer_reg = self.helper.register_customer(self.client)
        customer_token = customer_reg.json()["access_token"]
        customer_headers = self.helper.get_headers(customer_token)
        
        # Create, accept, and check in
        task_response = self.helper.create_task(self.client, customer_headers)
        task_id = task_response.json()["task_id"]
        
        self.client.post(
            f"/api/v1/workers/{worker_id}/accept-task/{task_id}",
            headers=worker_headers
        )
        
        self.client.post(
            f"/api/v1/workers/{worker_id}/check-in/{task_id}",
            json={"proof_photo_url": "https://example.com/checkin.jpg"},
            headers=worker_headers
        )
        
        # Check out
        response = self.client.post(
            f"/api/v1/workers/{worker_id}/check-out/{task_id}",
            json={"proof_photo_url": "https://example.com/checkout.jpg"},
            headers=worker_headers
        )
        
        assert response.status_code == 200
    
    def test_worker_stats(self):
        """Test fetching worker statistics"""
        worker_reg = self.helper.register_worker(self.client)
        token = worker_reg.json()["access_token"]
        headers = self.helper.get_headers(token)
        worker_id = worker_reg.json()["user_id"]
        
        response = self.client.get(
            f"/api/v1/workers/{worker_id}/stats",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tasks_completed" in data
        assert "rating" in data


def test_worker_integration_complete_flow(client):
    """Test complete worker flow: register -> locate -> accept task -> complete"""
    helper = TestHelper()
    
    # 1. Worker registration
    worker_reg = helper.register_worker(client)
    assert worker_reg.status_code == 200
    worker_token = worker_reg.json()["access_token"]
    worker_id = worker_reg.json()["user_id"]
    worker_headers = helper.get_headers(worker_token)
    
    # 2. Update location
    location_resp = client.put(
        f"/api/v1/workers/{worker_id}/location",
        json={"latitude": 28.7041, "longitude": 77.1025},
        headers=worker_headers
    )
    assert location_resp.status_code == 200
    
    # 3. Customer creates task
    customer_reg = helper.register_customer(client)
    customer_token = customer_reg.json()["access_token"]
    customer_headers = helper.get_headers(customer_token)
    
    task_resp = helper.create_task(client, customer_headers)
    assert task_resp.status_code == 200
    task_id = task_resp.json()["task_id"]
    
    # 4. Worker accepts task
    accept_resp = client.post(
        f"/api/v1/workers/{worker_id}/accept-task/{task_id}",
        headers=worker_headers
    )
    assert accept_resp.status_code == 200
    
    # 5. Check in
    checkin_resp = client.post(
        f"/api/v1/workers/{worker_id}/check-in/{task_id}",
        json={"proof_photo_url": "https://example.com/photo.jpg"},
        headers=worker_headers
    )
    assert checkin_resp.status_code == 200
    
    # 6. Check out (complete)
    checkout_resp = client.post(
        f"/api/v1/workers/{worker_id}/check-out/{task_id}",
        json={"proof_photo_url": "https://example.com/photo2.jpg"},
        headers=worker_headers
    )
    assert checkout_resp.status_code == 200
