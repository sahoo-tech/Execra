from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app
from core.plugins.rule_loader import RulePlugin

client = TestClient(app)

def test_get_plugins_empty():
    with patch("api.routes.plugins.plugin_loader") as mock_loader:
        mock_loader.plugins = []
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        assert response.json() == []

def test_get_plugins_populated():
    mock_plugin = RulePlugin(
        name="Test Plugin Route",
        version="2.0.0",
        trigger_keywords=["test", "route"],
        trigger_objects=["ui_element"],
        severity="critical",
        instruction_template="Fix the route.",
        enabled=True
    )
    with patch("api.routes.plugins.plugin_loader") as mock_loader:
        mock_loader.plugins = [mock_plugin]
        response = client.get("/api/v1/plugins")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Plugin Route"
        assert data[0]["version"] == "2.0.0"
        assert data[0]["severity"] == "critical"
        assert data[0]["enabled"] is True
        assert data[0]["trigger_keywords"] == ["test", "route"]
        assert data[0]["trigger_objects"] == ["ui_element"]

def test_get_plugins_real_load():
    # Test without mocking to check overall integrity with default rules
    response = client.get("/api/v1/plugins")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "name" in data[0]
        assert "version" in data[0]
        assert "severity" in data[0]
