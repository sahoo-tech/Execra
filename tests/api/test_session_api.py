import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from api.main import app

client = TestClient(app)

@patch("api.routes.session.action_logger.get_actions_by_session", new_callable=AsyncMock)
@patch("api.routes.session.NotionExporter")
@patch("api.routes.session.settings")
def test_export_session_success(mock_settings, mock_exporter_class, mock_get_actions):
    mock_settings.NOTION_API_KEY = "test-key"
    mock_settings.NOTION_PARENT_PAGE_ID = "test-page"
    
    mock_get_actions.return_value = ["mock_action"]
    
    mock_exporter_instance = MagicMock()
    mock_exporter_instance.export_session.return_value = "https://notion.so/test-page"
    mock_exporter_class.return_value = mock_exporter_instance
    
    response = client.post("/api/v1/session/export/notion", json={"session_id": "test-session"})
    
    assert response.status_code == 200
    assert response.json() == {"message": "Session exported successfully to Notion", "url": "https://notion.so/test-page"}
    mock_get_actions.assert_called_once_with("test-session")
    mock_exporter_instance.export_session.assert_called_once_with("test-session", "test-page", ["mock_action"])

@patch("api.routes.session.settings")
def test_export_session_missing_config(mock_settings):
    mock_settings.NOTION_API_KEY = ""
    mock_settings.NOTION_PARENT_PAGE_ID = ""
    
    response = client.post("/api/v1/session/export/notion", json={"session_id": "test-session"})
    assert response.status_code == 500
    assert "Notion configuration is missing" in response.json()["detail"]
