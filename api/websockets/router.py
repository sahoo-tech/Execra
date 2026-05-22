import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websockets.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)
router = APIRouter()
manager = ConnectionManager()


async def broadcast_action_log(action) -> None:
    """Callback triggered by action_logger.log_action() to broadcast the event to all WebSocket clients."""
    payload = {
        "event": "action_logged",
        "version": "1.0.0",
        "data": {
            "id": action.id,
            "session_id": action.session_id,
            "timestamp": action.timestamp.isoformat(),
            "type": action.type,
            "description": action.description,
            "domain": action.domain,
            "was_guided": action.was_guided,
            "guidance_confidence": action.guidance_confidence,
        },
    }
    await manager.broadcast(payload)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Handle incoming text messages
            data = await websocket.receive_text()
            if data == "hello":
                await websocket.send_json(
                    {
                        "event": "handshake",
                        "version": "1.0.0",
                        "message": "Connected to ws://localhost:8000/ws",
                    }
                )
            else:
                await websocket.send_json({"event": "echo", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket communication error: {e}")
        manager.disconnect(websocket)
