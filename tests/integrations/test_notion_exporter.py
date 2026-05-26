import pytest
from unittest.mock import MagicMock, patch
from core.integrations.notion_exporter import NotionExporter
from core.hybrid.action_logger import ActionRecord
from datetime import datetime

@pytest.fixture
def mock_notion_client():
    with patch("core.integrations.notion_exporter.Client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance

def test_export_session(mock_notion_client):
    mock_notion_client.pages.create.return_value = {"url": "https://notion.so/test-page"}
    
    exporter = NotionExporter("test-key")
    actions = [
        ActionRecord(
            id="1", session_id="test-session", timestamp=datetime.now(),
            type="click", description="test click", domain="digital",
            was_guided=True, guidance_confidence=0.95
        )
    ]
    
    url = exporter.export_session("test-session", "test-page-id", actions)
    
    assert url == "https://notion.so/test-page"
    mock_notion_client.pages.create.assert_called_once()
    
    call_kwargs = mock_notion_client.pages.create.call_args.kwargs
    assert call_kwargs["parent"] == {"page_id": "test-page-id"}
    assert call_kwargs["properties"]["title"][0]["text"]["content"] == "Execra Session: test-session"
    assert len(call_kwargs["children"]) == 1
    
    table_rows = call_kwargs["children"][0]["table"]["children"]
    assert len(table_rows) == 2
    
    # Check data mapping in row
    data_row = table_rows[1]["table_row"]["cells"]
    assert data_row[1][0]["text"]["content"] == "click"
    assert data_row[4][0]["text"]["content"] == "Yes"
    assert data_row[5][0]["text"]["content"] == "0.95"
