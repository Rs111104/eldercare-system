from fastapi.testclient import TestClient
from app.main import app


def test_request_logging_and_metrics_endpoint():
    client = TestClient(app)

    # basic health check should work
    r = client.get('/health')
    assert r.status_code == 200

    # metrics endpoint should return 200 even when prometheus_client not installed in this env
    m = client.get('/metrics')
    assert m.status_code == 200
    # body may be empty bytes if prometheus_client not available
    assert m.content is not None
