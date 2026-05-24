"""
Comprehensive Testing Utilities for ElderCare System
Includes test data generation, API testing, and load testing
"""

import pytest
import asyncio
import json
from datetime import datetime
from typing import Dict, List
from httpx import AsyncClient
import random
import string


class TestDataGenerator:
    """Generate test data for system testing"""

    @staticmethod
    def generate_customer(index: int = 1) -> Dict:
        """Generate customer test data"""
        return {
            "name": f"Test Customer {index}",
            "email": f"customer{index}@test.com",
            "phone_number": f"9999999{str(index).zfill(3)}",
            "password": "testpass123",
            "address": f"Test Address {index}, City, ZIP",
            "age": 65 + (index % 30),
        }

    @staticmethod
    def generate_worker(index: int = 1) -> Dict:
        """Generate worker test data"""
        return {
            "name": f"Test Worker {index}",
            "email": f"worker{index}@test.com",
            "phone_number": f"8888888{str(index).zfill(3)}",
            "password": "testpass123",
            "service_types": ["medicine", "help", "visit", "cleaning"],
            "experience_years": random.randint(1, 10),
            "hourly_rate": random.choice([250, 300, 350, 400, 450, 500]),
            "bio": f"Experienced worker with {random.randint(1, 10)} years in eldercare",
            "languages": ["Hindi", "English"],
            "availability": random.choice(["full_time", "part_time", "flexible"]),
        }

    @staticmethod
    def generate_task() -> Dict:
        """Generate task test data"""
        service_types = ["medicine", "help", "visit", "cleaning"]
        return {
            "title": "Test Task: " + "".join(random.choices(string.ascii_letters, k=10)),
            "description": "This is a test task for system validation",
            "service_type": random.choice(service_types),
            "location": f"Test Location {random.randint(1, 100)}",
            "effort_level": random.randint(1, 5),
            "mode": random.choice(["quick", "scheduled"]),
            "estimated_price": random.uniform(500, 2000),
        }

    @staticmethod
    def generate_batch_customers(count: int) -> List[Dict]:
        """Generate multiple customer records"""
        return [TestDataGenerator.generate_customer(i) for i in range(1, count + 1)]

    @staticmethod
    def generate_batch_workers(count: int) -> List[Dict]:
        """Generate multiple worker records"""
        return [TestDataGenerator.generate_worker(i) for i in range(1, count + 1)]


class APITestClient:
    """Helper class for API testing"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = AsyncClient(base_url=base_url)
        self.token = None
        self.user_id = None

    async def register_customer(self, data: Dict) -> Dict:
        """Register a customer"""
        response = await self.client.post(
            "/api/v1/auth/register/customer",
            json=data
        )
        assert response.status_code == 201
        result = response.json()
        self.token = result.get("access_token")
        self.user_id = result.get("user_id")
        return result

    async def register_worker(self, data: Dict) -> Dict:
        """Register a worker"""
        response = await self.client.post(
            "/api/v1/auth/register/worker",
            json=data
        )
        assert response.status_code == 201
        result = response.json()
        self.token = result.get("access_token")
        self.user_id = result.get("user_id")
        return result

    async def login(self, phone_number: str, password: str) -> Dict:
        """Login user"""
        response = await self.client.post(
            "/api/v1/auth/login",
            json={
                "phone_number": phone_number,
                "password": password
            }
        )
        assert response.status_code == 200
        result = response.json()
        self.token = result.get("access_token")
        self.user_id = result.get("user_id")
        return result

    async def create_task(self, data: Dict) -> Dict:
        """Create a task"""
        response = await self.client.post(
            "/api/v1/tasks/create",
            json=data,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 201
        return response.json()

    async def get_task(self, task_id: str) -> Dict:
        """Get task details"""
        response = await self.client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200
        return response.json()

    async def accept_task(self, task_id: str) -> Dict:
        """Accept task as worker"""
        response = await self.client.post(
            f"/api/v1/workers/{self.user_id}/accept-task/{task_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        assert response.status_code == 200
        return response.json()

    async def calculate_pricing(self, data: Dict) -> Dict:
        """Calculate task pricing"""
        response = await self.client.post(
            "/api/v1/pricing/calculate",
            json=data
        )
        assert response.status_code == 200
        return response.json()

    async def close(self):
        """Close the client"""
        await self.client.aclose()


class LoadTestRunner:
    """Run load tests on the system"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "response_times": [],
            "errors": []
        }

    async def load_test_register(self, num_customers: int = 100) -> Dict:
        """Load test customer registration"""
        print(f"Starting load test: Registering {num_customers} customers...")
        
        for i in range(num_customers):
            client = APITestClient(self.base_url)
            try:
                start_time = datetime.utcnow()
                await client.register_customer(TestDataGenerator.generate_customer(i))
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                self.results["total_requests"] += 1
                self.results["successful"] += 1
                self.results["response_times"].append(response_time)
                
                if i % 10 == 0:
                    print(f"Progress: {i}/{num_customers} registrations completed")
            except Exception as e:
                self.results["total_requests"] += 1
                self.results["failed"] += 1
                self.results["errors"].append(str(e))
            finally:
                await client.close()
        
        return self._calculate_stats()

    async def load_test_task_creation(self, num_tasks: int = 50) -> Dict:
        """Load test task creation"""
        print(f"Starting load test: Creating {num_tasks} tasks...")
        
        # First register a customer
        client = APITestClient(self.base_url)
        await client.register_customer(TestDataGenerator.generate_customer())
        
        for i in range(num_tasks):
            try:
                start_time = datetime.utcnow()
                await client.create_task(TestDataGenerator.generate_task())
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                self.results["total_requests"] += 1
                self.results["successful"] += 1
                self.results["response_times"].append(response_time)
                
                if i % 10 == 0:
                    print(f"Progress: {i}/{num_tasks} tasks created")
            except Exception as e:
                self.results["total_requests"] += 1
                self.results["failed"] += 1
                self.results["errors"].append(str(e))
        
        await client.close()
        return self._calculate_stats()

    async def load_test_pricing(self, num_calculations: int = 100) -> Dict:
        """Load test pricing calculations"""
        print(f"Starting load test: {num_calculations} pricing calculations...")
        
        client = APITestClient(self.base_url)
        
        for i in range(num_calculations):
            try:
                start_time = datetime.utcnow()
                await client.calculate_pricing({
                    "distance_km": random.uniform(1, 50),
                    "service_type": random.choice(["medicine", "help", "visit", "cleaning"]),
                    "effort_level": random.randint(1, 5),
                    "urgency_multiplier": random.uniform(1.0, 1.5)
                })
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                self.results["total_requests"] += 1
                self.results["successful"] += 1
                self.results["response_times"].append(response_time)
                
                if i % 25 == 0:
                    print(f"Progress: {i}/{num_calculations} calculations completed")
            except Exception as e:
                self.results["total_requests"] += 1
                self.results["failed"] += 1
                self.results["errors"].append(str(e))
        
        await client.close()
        return self._calculate_stats()

    def _calculate_stats(self) -> Dict:
        """Calculate statistics from test results"""
        if not self.results["response_times"]:
            return self.results
        
        times = sorted(self.results["response_times"])
        
        return {
            **self.results,
            "success_rate": (self.results["successful"] / self.results["total_requests"] * 100) if self.results["total_requests"] > 0 else 0,
            "avg_response_time": sum(times) / len(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "p95_response_time": times[int(len(times) * 0.95)] if len(times) > 0 else 0,
            "p99_response_time": times[int(len(times) * 0.99)] if len(times) > 0 else 0,
        }


class SystemHealthMonitor:
    """Monitor system health during testing"""

    @staticmethod
    async def check_api_health(base_url: str = "http://localhost:8000") -> Dict:
        """Check API health endpoint"""
        client = AsyncClient(base_url=base_url)
        try:
            response = await client.get("/api/v1/health")
            health = response.json() if response.status_code == 200 else {"status": "unhealthy"}
            return health
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
        finally:
            await client.aclose()

    @staticmethod
    async def check_database_connection(base_url: str = "http://localhost:8000") -> Dict:
        """Check database connection"""
        client = AsyncClient(base_url=base_url)
        try:
            response = await client.get("/api/v1/admin/health")
            health = response.json() if response.status_code == 200 else {"database": "disconnected"}
            return health
        except Exception as e:
            return {"database": "disconnected", "error": str(e)}
        finally:
            await client.aclose()


# Example test functions
@pytest.mark.asyncio
async def test_customer_registration():
    """Test customer registration flow"""
    client = APITestClient()
    customer_data = TestDataGenerator.generate_customer()
    result = await client.register_customer(customer_data)
    
    assert result["user_id"]
    assert result["access_token"]
    await client.close()


@pytest.mark.asyncio
async def test_task_creation_and_pricing():
    """Test task creation and pricing calculation"""
    client = APITestClient()
    
    # Register customer
    await client.register_customer(TestDataGenerator.generate_customer())
    
    # Create task
    task_data = TestDataGenerator.generate_task()
    task = await client.create_task(task_data)
    assert task["task_id"]
    
    # Calculate pricing
    pricing = await client.calculate_pricing({
        "distance_km": 5,
        "service_type": task_data["service_type"],
        "effort_level": task_data["effort_level"],
        "urgency_multiplier": 1.0
    })
    assert pricing["estimated_price"] > 0
    
    await client.close()


@pytest.mark.asyncio
async def test_worker_task_workflow():
    """Test complete worker task workflow"""
    customer_client = APITestClient()
    worker_client = APITestClient()
    
    # Register customer and create task
    await customer_client.register_customer(TestDataGenerator.generate_customer())
    task = await customer_client.create_task(TestDataGenerator.generate_task())
    task_id = task["task_id"]
    
    # Register worker
    await worker_client.register_worker(TestDataGenerator.generate_worker())
    
    # Worker accepts task
    result = await worker_client.accept_task(task_id)
    assert result["status"] == "assigned"
    
    await customer_client.close()
    await worker_client.close()


if __name__ == "__main__":
    # Run example load tests
    asyncio.run(main_load_tests())


async def main_load_tests():
    """Run all load tests"""
    runner = LoadTestRunner()
    
    print("\n=== LOAD TEST RESULTS ===\n")
    
    print("1. Registration Load Test")
    results = await runner.load_test_register(num_customers=50)
    print_results(results)
    
    print("\n2. Task Creation Load Test")
    runner.results = {"total_requests": 0, "successful": 0, "failed": 0, "response_times": [], "errors": []}
    results = await runner.load_test_task_creation(num_tasks=50)
    print_results(results)
    
    print("\n3. Pricing Calculation Load Test")
    runner.results = {"total_requests": 0, "successful": 0, "failed": 0, "response_times": [], "errors": []}
    results = await runner.load_test_pricing(num_calculations=100)
    print_results(results)


def print_results(results: Dict):
    """Print load test results"""
    print(f"""
    Total Requests: {results.get('total_requests')}
    Successful: {results.get('successful')}
    Failed: {results.get('failed')}
    Success Rate: {results.get('success_rate', 0):.2f}%
    
    Response Times:
    - Average: {results.get('avg_response_time', 0):.3f}s
    - Min: {results.get('min_response_time', 0):.3f}s
    - Max: {results.get('max_response_time', 0):.3f}s
    - P95: {results.get('p95_response_time', 0):.3f}s
    - P99: {results.get('p99_response_time', 0):.3f}s
    """)
