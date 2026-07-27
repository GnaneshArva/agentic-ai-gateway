from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agentic-ai-gateway"


def test_readiness_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"


def test_list_routes_endpoint():
    response = client.get("/api/v1/gateway/routes")
    assert response.status_code == 200
    data = response.json()
    assert "default_route" in data
    assert len(data["routes"]) > 0


def test_policy_status_endpoint():
    response = client.get("/api/v1/gateway/policies/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_policies" in data
    assert "limits" in data


def test_process_request_endpoint_success():
    payload = {
        "prompt": "Plan a trip to Rome",
        "provider": "OpenAI",
        "model": "gpt-4o",
        "user_id": "test_user_http",
    }
    response = client.post("/api/v1/gateway/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["metadata"]["request_id"] is not None
    assert "X-Request-ID" in response.headers


def test_process_request_endpoint_validation_error():
    # Empty prompt and messages
    payload = {}
    response = client.post("/api/v1/gateway/process", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
