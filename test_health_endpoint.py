import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that the /health endpoint returns {'status': 'ok'}"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_health_live_endpoint():
    """Test that the /health/live endpoint returns {'status': 'ok'}"""
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "component": "live"}

def test_health_ready_endpoint():
    """Test that the /health/ready endpoint returns status based on checks"""
    response = client.get("/health/ready")
    # The response could be 200 or 503 depending on the health checks
    assert response.status_code in [200, 503]
    json_response = response.json()
    assert "status" in json_response
    assert "component" in json_response
    assert json_response["component"] == "ready"
    assert "checks" in json_response

def test_health_deps_endpoint():
    """Test that the /health/deps endpoint returns status of dependencies"""
    response = client.get("/health/deps")
    # The response could be 200 or 500 depending on the dependency checks
    assert response.status_code in [200, 500]
    json_response = response.json()
    assert "status" in json_response
    assert "component" in json_response
    assert json_response["component"] == "deps"
    assert "checks" in json_response

if __name__ == "__main__":
    test_health_endpoint()
    test_health_live_endpoint()
    test_health_ready_endpoint()
    test_health_deps_endpoint()
    print("All health endpoint tests passed!")