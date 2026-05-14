from typing import Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.hybrid.mode_manager import ModeManager

router = APIRouter();

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