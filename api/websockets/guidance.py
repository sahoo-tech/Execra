from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.hybrid.mode_manager import ModeManager

router = APIRouter()

class ConnectionManager:
    # Will manage the active Websocket Connection
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        # accepts and registers WebSocket connection
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        # removes from active connections
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal(self, message: dict[str, Any], websocket: WebSocket) -> None:
        # sends JSON message to one specific client
        await websocket.send_json(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        # sends JSON message to all connected clients
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected_connections.append(connection)
        
        for connection in disconnected_connections:
            self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/guidance")
async def guidance_websocket(websocket: WebSocket) -> None:
    # main execra guidance communication endpoint
    await manager.connect(websocket)
    await manager.send_personal(
        {
            "event": "connected",
            "payload": {
                "status" : "ok",
            },
        },
        websocket,
    )

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload", {})
            
            if event == "user_action":
                print(f"User Action received: {payload}")

            elif event == "ask":
                question = payload.get("question", "")

                await manager.send_personal(
                    {
                        "event": "guidance",
                        "payload": {
                            "instruction" : (
                                f"Analyzing request: {question}"
                            ),
                            "confidence" : 0.87,
                            "source": [
                                "llm",
                                "rule_engine",
                            ],
                            "reasoning": (
                                "Generated based on user query."
                            ),
                            "mode" : "safe",
                            "step" : 1,
                            "total_steps": 3,
                        },
                    },
                    websocket,
                )

            elif event == "mode_switch":
                mode = payload.get("mode")
                ModeManager.switch_mode(mode)

                await manager.broadcast(
                    {
                        "event": "mode_switch",
                        "payload": {
                            "mode": mode,
                        },
                    }
                )

            else:
                await manager.send_personal(
                    {
                        "event": "error",
                        "payload": {
                            "message": (
                                f"Unknown event type: {event}"
                            ),
                        },
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as exc:
        await manager.send_personal(
            {
                "event": "error",
                "payload": {
                    "message": str(exc),
                },
            },
            websocket,
        )

        manager.disconnect(websocket)