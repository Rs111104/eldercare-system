"""
Test utilities and fixtures for the application
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import json


class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def customer(phone="+919876543210"):
        return {
            "phone_number": phone,
            "password": "TestPassword123!",
            "email": "customer@test.com"
        }
    
    @staticmethod
    def worker(phone="+918765432109"):
        return {
            "phone_number": phone,
            "password": "TestPassword123!",
            "service_types": ["medicine", "help"],
            "email": "worker@test.com"
        }
    
    @staticmethod
    def task():
        return {
            "title": "Test Task",
            "description": "This is a test task",
            "task_type": "medicine",
            "mode": "quick",
            "urgency_level": 3,
            "location": "Test Location"
        }
    
    @staticmethod
    def pricing_config():
        return {
            "service_type": "medicine",
            "base_price": 50,
            "distance_charge_per_km": 5,
            "effort_multiplier": 1.0
        }


class TestHelper:
    """Helper methods for testing"""
    
    @staticmethod
    def register_customer(client: TestClient, **kwargs):
        """Register a customer and return response"""
        data = TestDataFactory.customer(**kwargs)
        response = client.post(
            f"{settings.API_V1_STR}/auth/register/customer",
            json=data
        )
        return response
    
    @staticmethod
    def register_worker(client: TestClient, **kwargs):
        """Register a worker and return response"""
        data = TestDataFactory.worker(**kwargs)
        response = client.post(
            f"{settings.API_V1_STR}/auth/register/worker",
            json=data
        )
        return response
    
    @staticmethod
    def login(client: TestClient, phone: str, password: str):
        """Login and return token"""
        response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"phone_number": phone, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    @staticmethod
    def get_headers(token: str):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    @staticmethod
    def create_task(client: TestClient, headers: dict, **kwargs):
        """Create a task and return response"""
        data = TestDataFactory.task()
        data.update(kwargs)
        response = client.post(
            f"{settings.API_V1_STR}/tasks/create",
            json=data,
            headers=headers
        )
        return response


class APITestBase:
    """Base class for API tests with setup/teardown"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client and data"""
        self.client = TestClient(app)
        self.helper = TestHelper()
        self.factory = TestDataFactory()
        yield
    
    def assert_response_structure(self, response, expected_keys: list):
        """Assert response JSON has expected keys"""
        assert response.status_code == 200
        data = response.json()
        for key in expected_keys:
            assert key in data, f"Missing key '{key}' in response"


class MockExternalServices:
    """Mock external services for testing"""
    
    @staticmethod
    def mock_openai_whisper():
        """Mock OpenAI Whisper transcription"""
        return "Test transcription of audio file"
    
    @staticmethod
    def mock_gpt4_classification():
        """Mock GPT-4 task classification"""
        return {
            "title": "Medicine Delivery",
            "task_type": "medicine",
            "urgency_level": 3,
            "effort_level": 2
        }
    
    @staticmethod
    def mock_whatsapp_message():
        """Mock WhatsApp incoming message"""
        return {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "919876543210",
                            "type": "text",
                            "text": {"body": "Need help"}
                        }]
                    }
                }]
            }]
        }


def assert_task_structure(task: dict):
    """Assert task has required fields"""
    required_fields = [
        "task_id", "title", "description", "task_type",
        "status", "price", "urgency_level"
    ]
    for field in required_fields:
        assert field in task, f"Missing field '{field}' in task"


def assert_worker_structure(worker: dict):
    """Assert worker has required fields"""
    required_fields = [
        "worker_id", "phone_number", "service_types",
        "rating", "is_verified"
    ]
    for field in required_fields:
        assert field in worker, f"Missing field '{field}' in worker"


def assert_payout_structure(payout: dict):
    """Assert payout has required fields"""
    required_fields = [
        "payout_id", "task_id", "worker_id",
        "immediate_payout", "verification_payout", "status"
    ]
    for field in required_fields:
        assert field in payout, f"Missing field '{field}' in payout"
