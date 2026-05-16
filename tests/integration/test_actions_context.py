import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from api.main import app
from core.hybrid.action_logger import action_logger, ActionRecord
import api.routes.context as context_module


client = TestClient(app)


def setup_function():
    """Reset action log and context before every test."""
    action_logger._stack.clear()
    action_logger._undone_ids.clear()
    context_module._current_context = None


# ---------------------------------------------------------------------------
# GET /api/v1/actions
# ---------------------------------------------------------------------------

def test_get_actions_empty():
    response = client.get("/api/v1/actions")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["actions"] == []


# ---------------------------------------------------------------------------
# POST /api/v1/actions/undo
# ---------------------------------------------------------------------------

def test_undo_returns_409_when_empty():
    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 409
    assert "Nothing to undo" in response.json()["detail"]


def test_undo_returns_409_when_all_actions_are_non_undoable():
    action = ActionRecord(
        id="act_999",
        session_id="sess_001",
        timestamp=datetime.now(),
        type="screen_read",
        description="Non-undoable observation",
        domain="digital",
        was_guided=False,
        guidance_confidence=None,
        is_undoable=False,
    )
    action_logger._stack.append(action)

    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 409


def test_undo_returns_undone_action():
    action = ActionRecord(
        id="act_001",
        session_id="sess_001",
        timestamp=datetime.now(),
        type="code_edit",
        description="Modified line 42",
        domain="digital",
        was_guided=True,
        guidance_confidence=0.9,
        is_undoable=True,
        undo_instruction="Revert line 42 to its previous value",
    )
    action_logger._stack.append(action)

    response = client.post("/api/v1/actions/undo")
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "Last action undone successfully."
    assert data["action_undone"]["id"] == "act_001"
    assert data["action_undone"]["description"] == "Modified line 42"
    assert data["action_undone"]["undo_instruction"] == "Revert line 42 to its previous value"


def test_double_undo_returns_409_on_second_call():
    action = ActionRecord(
        id="act_001",
        session_id="sess_001",
        timestamp=datetime.now(),
        type="code_edit",
        description="Modified line 42",
        domain="digital",
        was_guided=True,
        guidance_confidence=0.9,
        is_undoable=True,
        undo_instruction="Revert line 42",
    )
    action_logger._stack.append(action)

    first = client.post("/api/v1/actions/undo")
    second = client.post("/api/v1/actions/undo")

    assert first.status_code == 200
    assert second.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/actions/replay
# ---------------------------------------------------------------------------

def test_replay_returns_empty_list_for_unknown_session():
    response = client.post(
        "/api/v1/actions/replay",
        json={"session_id": "nonexistent", "speed": 1.0},
    )
    # Endpoint reads from SQLite (not in-memory stack) — empty result expected.
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "nonexistent"
    assert data["total"] == 0
    assert data["actions"] == []


def test_replay_rejects_non_positive_speed():
    response = client.post(
        "/api/v1/actions/replay",
        json={"session_id": "sess_001", "speed": 0},
    )
    assert response.status_code == 400
    assert "speed" in response.json()["detail"].lower()

    response = client.post(
        "/api/v1/actions/replay",
        json={"session_id": "sess_001", "speed": -2.5},
    )
    assert response.status_code == 400


def test_replay_requires_session_id():
    response = client.post("/api/v1/actions/replay", json={"speed": 1.0})
    assert response.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# WebSocket /ws/replay/{session_id}
# ---------------------------------------------------------------------------

def test_websocket_replay_empty_session_sends_complete():
    """An empty session should immediately receive replay_complete."""
    with client.websocket_connect("/ws/replay/empty_session") as ws:
        data = ws.receive_json()
    assert data["event"] == "replay_complete"


def test_websocket_replay_invalid_speed_sends_error():
    with client.websocket_connect("/ws/replay/sess_001?speed=-1") as ws:
        data = ws.receive_json()
    assert data["event"] == "error"
    assert "speed" in data["detail"].lower()


# ---------------------------------------------------------------------------
# GET /api/v1/context
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# DELETE /api/v1/context
# ---------------------------------------------------------------------------

def test_delete_context_returns_success():
    response = client.delete("/api/v1/context")
    assert response.status_code == 200
    assert response.json()["message"] == "Session context cleared."


def test_delete_context_clears_deque():
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
            is_undoable=True,
        )
    )

    client.delete("/api/v1/context")

    assert len(action_logger._stack) == 0
    assert len(action_logger._undone_ids) == 0
