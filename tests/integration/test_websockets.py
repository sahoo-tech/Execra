import pytest
import asyncio
from datetime import datetime
from fastapi.testclient import TestClient
from api.main import app
from core.hybrid.action_logger import ActionRecord
from api.websockets.router import manager, broadcast_action_log, websocket_endpoint

def test_websocket_handshake_and_echo():
    client = TestClient(app)
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("hello")
        data = websocket.receive_json()
        assert data["event"] == "handshake"
        assert "Connected to ws://localhost:8000/ws" in data["message"]

        websocket.send_text("test_msg")
        data = websocket.receive_json()
        assert data["event"] == "echo"
        assert data["data"] == "test_msg"

@pytest.mark.asyncio
async def test_manager_broadcast():
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
            self.accepted = False

        async def accept(self):
            self.accepted = True

        async def send_json(self, message):
            self.sent_messages.append(message)

    mock_ws = MockWebSocket()
    await manager.connect(mock_ws)  # type: ignore
    assert mock_ws.accepted is True
    assert mock_ws in manager.active_connections

    msg = {"test": "data"}
    await manager.broadcast(msg)
    assert mock_ws.sent_messages == [msg]

    manager.disconnect(mock_ws)  # type: ignore
    assert mock_ws not in manager.active_connections

@pytest.mark.asyncio
async def test_manager_broadcast_exception():
    class BrokenWebSocket:
        def __init__(self):
            self.accepted = False
        async def accept(self):
            self.accepted = True
        async def send_json(self, message):
            raise RuntimeError("Connection broken")

    broken_ws = BrokenWebSocket()
    await manager.connect(broken_ws)  # type: ignore
    assert broken_ws in manager.active_connections

    await manager.broadcast({"some": "data"})
    # The broken connection should be automatically cleaned up
    assert broken_ws not in manager.active_connections

@pytest.mark.asyncio
async def test_websocket_endpoint_exception():
    class FaultyWebSocket:
        def __init__(self):
            self.accepted = False
            self.disconnected = False
        async def accept(self):
            self.accepted = True
        async def receive_text(self):
            raise ValueError("Unexpected disconnect/error")
        async def close(self):
            self.disconnected = True
            
    faulty_ws = FaultyWebSocket()
    await websocket_endpoint(faulty_ws)  # type: ignore
    assert faulty_ws not in manager.active_connections

@pytest.mark.asyncio
async def test_broadcast_action_log_callback():
    class MockWebSocket:
        def __init__(self):
            self.sent_messages = []
        async def accept(self):
            pass
        async def send_json(self, message):
            self.sent_messages.append(message)

    mock_ws = MockWebSocket()
    await manager.connect(mock_ws)  # type: ignore

    record = ActionRecord(
        id="action-abc",
        session_id="session-123",
        timestamp=datetime.now(),
        type="keypress",
        description="Typed enter",
        domain="digital",
        was_guided=True,
        guidance_confidence=0.95
    )

    await broadcast_action_log(record)
    assert len(mock_ws.sent_messages) == 1
    payload = mock_ws.sent_messages[0]
    assert payload["event"] == "action_logged"
    assert payload["data"]["id"] == "action-abc"
    assert payload["data"]["was_guided"] is True
    assert payload["data"]["guidance_confidence"] == 0.95

    manager.disconnect(mock_ws)  # type: ignore
