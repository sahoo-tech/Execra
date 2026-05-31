from datetime import datetime

from fastapi.testclient import TestClient

import api.routes.context as context_module
from api.main import app
from core.hybrid.action_logger import action_logger

client = TestClient(app)


def setup_function():
    """Reset in-memory action log and context before every test."""
    action_logger.clear()
    context_module._current_context = None


def test_get_actions_empty():
    response = client.get("/api/v1/actions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["actions"] == []


def test_undo_returns_409_when_empty():
    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 409
    assert "Nothing in the undo stack" in response.json()["detail"]


def test_undo_returns_undone_action():
    # Create an undoable action via the API endpoint.
    response = client.post(
        "/api/v1/actions",
        json={
            "type": "code_edit",
            "description": "Modified line 42",
            "session_id": "sess_001",
            "domain": "digital",
            "was_guided": True,
            "guidance_confidence": 0.9,
            "is_undoable": True,
        },
    )
    assert response.status_code == 200

    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Last action undone successfully."
    assert data["action_undone"]["description"] == "Modified line 42"
    assert data["action_undone"]["undone"] is True


def test_get_context_returns_404_when_empty():
    response = client.get("/api/v1/context")
    assert response.status_code == 404
    assert "No active session context" in response.json()["detail"]


def test_get_context_returns_active_context():
    from api.routes.context import SessionContext

    context_module._current_context = SessionContext(
        session_id="sess_001",
        task_type="code_debugging",
        current_step=4,
        total_steps=9,
        step_description="Fix the null check",
        error_history=[],
        domain="digital",
        started_at=datetime.now(),
    )

    response = client.get("/api/v1/context")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == "sess_001"
    assert data["task_type"] == "code_debugging"


def test_delete_context_returns_success():
    response = client.delete("/api/v1/context")
    assert response.status_code == 200
    assert response.json()["message"] == "Session context cleared."


def test_delete_context_clears_session_actions():
    from api.routes.context import SessionContext

    context_module._current_context = SessionContext(
        session_id="sess_001",
        task_type="code_debugging",
        current_step=1,
        total_steps=5,
        step_description="Test step",
        error_history=[],
        domain="digital",
        started_at=datetime.now(),
    )

    # Create a session action via the API.
    client.post(
        "/api/v1/actions",
        json={
            "type": "code_edit",
            "description": "Test",
            "session_id": "sess_001",
            "domain": "digital",
            "was_guided": True,
            "guidance_confidence": 0.9,
        },
    )

    client.delete("/api/v1/context")

    assert action_logger.total_actions() == 0
