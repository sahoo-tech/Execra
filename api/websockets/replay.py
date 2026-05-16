from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.hybrid.action_logger import action_logger

router = APIRouter()


@router.websocket("/ws/replay/{session_id}")
async def replay_websocket(
    websocket: WebSocket, session_id: str, speed: float = 1.0
):
    """Stream session actions as ``replay_action`` WebSocket events.

    Connect with optional ``?speed=<float>`` query parameter (default 1.0).
    Sends one JSON message per action, honouring original timing divided by
    *speed*.  Closes with a ``replay_complete`` event when all actions are
    sent.

    Error cases (invalid speed, unexpected exception) are reported as a JSON
    ``{"event": "error", "detail": "..."}`` message before closing.
    """
    await websocket.accept()
    try:
        if speed <= 0:
            await websocket.send_json(
                {"event": "error", "detail": "Replay speed must be > 0."}
            )
            return

        async for action in action_logger.replay_session(session_id, speed=speed):
            await websocket.send_json(
                {
                    "event": "replay_action",
                    "action": {
                        "id": action.id,
                        "session_id": action.session_id,
                        "type": action.type,
                        "description": action.description,
                        "domain": action.domain,
                        "timestamp": action.timestamp.isoformat(),
                        "was_guided": action.was_guided,
                        "is_undoable": action.is_undoable,
                        "undo_instruction": action.undo_instruction,
                        "interval": action.interval,
                    },
                }
            )

        await websocket.send_json({"event": "replay_complete"})

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"event": "error", "detail": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
