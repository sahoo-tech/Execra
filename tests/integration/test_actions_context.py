import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

import api.routes.context as context_module
from api.main import app
from core.hybrid.action_logger import ActionRecord, action_logger

client = TestClient(app)
TEST_DB_PATH = "data/execra_test.db"


def setup_function():
    """Reset in-memory state and context before every test."""
    # Switch to a dedicated test database and clear all in-memory state.
    action_logger.db_path = TEST_DB_PATH
    action_logger.clear()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    context_module._current_context = None


def teardown_function():
    """Clean up the test database file after every test."""
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


def test_get_actions_empty():
    response = client.get("/api/v1/actions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["actions"] == []


def test_create_action():
    action_data = {
        "id": "act_post_001",
        "session_id": "sess_post_001",
        "timestamp": datetime.now().isoformat(),
        "type": "keystroke",
        "description": "Typed command",
        "domain": "digital",
        "was_guided": True,
        "guidance_confidence": 0.85,
    }
    response = client.post("/api/v1/actions", json=action_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Action logged successfully."
    assert response.json()["action"]["id"] == "act_post_001"
    assert len(action_logger._stack) == 1
    assert action_logger._stack[0].id == "act_post_001"


def test_undo_returns_409_when_empty():
    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 409
    assert "Nothing to undo" in response.json()["detail"]


def test_undo_returns_undone_action():
    # Create an undoable action via the API.
    action_data = {
        "id": "act_001",
        "session_id": "sess_001",
        "timestamp": datetime.now().isoformat(),
        "type": "code_edit",
        "description": "Modified line 42",
        "domain": "digital",
        "was_guided": True,
        "guidance_confidence": 0.9,
        "is_undoable": True,
    }
    client.post("/api/v1/actions", json=action_data)

    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Last action undone successfully."
    assert data["action_undone"]["id"] == "act_001"
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

    action_logger._stack.append(
        ActionRecord(
            id="act_001",
            session_id="sess_001",
            timestamp=datetime.now(),
            type="code_edit",
            description="Test",
            domain="digital",
            was_guided=True,
            guidance_confidence=0.9,
        )
    )
    action_logger._actions.append(action_logger._stack[-1])

    client.delete("/api/v1/context")

    assert len(action_logger._stack) == 0
    assert len(action_logger._actions) == 0
