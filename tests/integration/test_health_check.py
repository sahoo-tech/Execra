"""
Integration tests for health check endpoint.
"""

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Test that /api/v1/health returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "healthy" in data
    assert "checks" in data


def test_health_response_structure():
    """Test that health response has correct structure."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    assert isinstance(data["healthy"], bool)
    assert isinstance(data["checks"], dict)
    assert "db" in data["checks"]
    assert "redis" in data["checks"]


def test_health_checks_have_valid_values():
    """Test that health checks have 'ok' or 'error' status."""
    response = client.get("/api/v1/health")
    data = response.json()
    
    valid_values = ["ok", "error"]
    assert data["checks"]["db"] in valid_values
    assert data["checks"]["redis"] in valid_values
    