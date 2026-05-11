import pytest
from fastapi.testclient import TestClient

from api.main import app
from core.config import settings
from core.hybrid.mode_manager import mode_manager


@pytest.fixture
def client():
    mode_manager.current_mode = "passive"
    with TestClient(app) as test_client:
        yield test_client


def test_get_status(client):
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "running"
    assert data["version"] == app.version
    assert data["active_domain"] == "digital"
    assert data["active_mode"] == "passive"
    assert data["perception_fps"] == settings.SCREEN_CAPTURE_FPS
    assert data["llm_backend"] == settings.LLM_BACKEND
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0


def test_get_mode_default(client):
    response = client.get("/api/v1/mode")

    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "passive"
    assert data["description"]


def test_put_mode_valid(client):
    response = client.put("/api/v1/mode", json={"mode": "active"})

    assert response.status_code == 200
    data = response.json()

    assert data["mode"] == "active"
    assert data["description"]

    response = client.get("/api/v1/mode")
    assert response.json()["mode"] == "active"


def test_put_mode_invalid(client):
    response = client.put("/api/v1/mode", json={"mode": "invalid"})

    assert response.status_code == 400
