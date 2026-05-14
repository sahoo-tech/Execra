from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_websocket_connection() -> None:
    # test for successfull websocket connection
    with client.websocket_connect("/ws/guidance") as websocket:
        response = websocket.receive_json()

        assert response["event"] == "connected"
        assert response["payload"]["status"] == "ok"

def test_ask_event() -> None:
    # Test to ask event handling
    with client.websocket_connect("/ws/guidance") as websocket:
        websocket.receive_json()

        websocket.send_json(
            {
                "event": "ask",
                "payload": {
                    "question" : "What should I do next?",
                },
            }
        )

        response = websocket.receive_json()

        assert response["event"] == "guidance"
        assert "instruction" in response["payload"]

def test_unknown_event() -> None:
    # Test for invalid event handling
    with client.websocket_connect("/ws/guidance") as websocket:
        websocket.receive_json()

        websocket.send_json(
            {
                "event": "invalid_event",
                "payload": {},
            }
        )
        
        response = websocket.receive_json()

        assert response["event"] == "error"