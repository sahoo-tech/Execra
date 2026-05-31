from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_get_status_returns_200():
    response = client.get("/api/v1/status")
    assert response.status_code == 200

def test_get_status_has_correct_fields():
    response = client.get("/api/v1/status")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "active_domain" in data
    assert "active_mode" in data
    assert "perception_fps" in data
    assert "llm_backend" in data


def test_status_value_is_running():
    response = client.get("/api/v1/status")
    data = response.json()

    assert data["status"] == "running"

def test_get_mode_returns_200():
    response = client.get("/api/v1/mode")
    assert response.status_code == 200

def test_get_mode_has_correct_fields():
    response = client.get("/api/v1/mode")
    data = response.json()

    assert "mode" in data
    assert "description" in data

def test_put_mode_valid_returns_200():
    response = client.put("/api/v1/mode", json={"mode": "active"})
    assert response.status_code == 200
    assert response.json()["mode"] == "active"

def test_put_mode_invalid_returns_400():
    response = client.put("/api/v1/mode", json={"mode": "banana"})
    assert response.status_code == 400