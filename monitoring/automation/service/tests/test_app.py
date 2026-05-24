import json
from fastapi.testclient import TestClient
import importlib.util
from pathlib import Path
import os
import hmac
import hashlib

# Load the service app module directly to avoid package name conflicts with backend.app
service_app_path = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("service_app", str(service_app_path))
service_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_app)

client = TestClient(service_app.app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json() == {'status': 'ok'}

def test_receive_alert_list_shape():
    payload = [{"labels": {"alertname": "TestAlert", "severity": "warning", "instance": "local"}, "annotations": {"summary": "Test alert"}}]
    r = client.post('/alert', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['received'] == 1
    assert isinstance(data['details'], list)

def test_receive_alert_alerts_key_shape():
    payload = {"alerts": [{"labels": {"alertname": "TestAlert2", "severity": "critical"}, "annotations": {"summary": "Critical"}}]}
    r = client.post('/alert', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['received'] == 1


def test_signature_verification_success(monkeypatch):
    secret = "testing-secret"
    monkeypatch.setenv("ALERT_WEBHOOK_SECRET", secret)
    payload = [{"labels": {"alertname": "SignedAlert", "severity": "warning"}, "annotations": {"summary": "Signed"}}]
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {"X-Alert-Signature": sig}
    r = client.post('/alert', data=body, headers=headers)
    assert r.status_code == 200


def test_signature_verification_failure(monkeypatch):
    secret = "testing-secret"
    monkeypatch.setenv("ALERT_WEBHOOK_SECRET", secret)
    payload = [{"labels": {"alertname": "BadSignedAlert", "severity": "warning"}, "annotations": {"summary": "Bad"}}]
    body = json.dumps(payload).encode()
    # wrong signature
    headers = {"X-Alert-Signature": "sha256=deadbeef"}
    r = client.post('/alert', data=body, headers=headers)
    assert r.status_code == 401


def test_token_header_success(monkeypatch):
    secret = "testing-secret"
    monkeypatch.setenv("ALERT_WEBHOOK_SECRET", secret)
    payload = [{"labels": {"alertname": "TokenAlert", "severity": "warning"}, "annotations": {"summary": "Token"}}]
    body = json.dumps(payload).encode()
    headers = {"X-Alert-Token": secret}
    r = client.post('/alert', data=body, headers=headers)
    assert r.status_code == 200


def test_metrics_endpoint_contains_metrics():
    r = client.get('/metrics')
    assert r.status_code == 200
    text = r.text
    assert 'automation_alerts_received_total' in text
    assert 'automation_alert_processing_seconds' in text


def test_runbook_trigger_called(monkeypatch):
    called = {"count": 0}

    def fake_create_runbook(summary, labels, annotations):
        called["count"] += 1

    # replace the function in the loaded service module
    monkeypatch.setattr(service_app, "_create_runbook", fake_create_runbook)

    payload = [{"labels": {"alertname": "CriticalAlert", "severity": "critical"}, "annotations": {"summary": "CRIT"}}]
    body = json.dumps(payload).encode()
    r = client.post('/alert', data=body)
    assert r.status_code == 200
    assert called["count"] >= 1
