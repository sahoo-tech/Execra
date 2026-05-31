import logging
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections, handles connection/disconnection, and safe broadcasts."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and add it to the active pool."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("New WebSocket connection accepted.")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove connection from active pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info("WebSocket connection removed.")

    async def broadcast(self, message: dict) -> None:
        """Safely broadcast a JSON payload to all active connections.

        Stale/broken connections are cleaned up automatically.
        """
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except (WebSocketDisconnect, RuntimeError, Exception) as e:
                logger.warning(f"Failed to send websocket message. Removing stale connection: {e}")
                self.disconnect(connection)
