from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.hybrid.action_logger import action_logger

router = APIRouter()


class ReplayRequest(BaseModel):
    session_id: str
    speed: float = 1.0


@router.get("/actions")
async def get_actions(limit: int = 20, offset: int = 0):
    actions = await action_logger.get_history(limit=limit, offset=offset)
    return {
        "total": len(actions),
        "actions": actions,
    }


@router.post("/actions/undo")
async def undo_last_action():
    undone = action_logger.undo_last()

    if undone is None:
        raise HTTPException(
            status_code=409,
            detail="Nothing to undo. No undoable actions remain.",
        )

    return {
        "message": "Last action undone successfully.",
        "action_undone": {
            "id": undone.id,
            "description": undone.description,
            "undo_instruction": undone.undo_instruction,
        },
    }


@router.post("/actions/replay")
async def replay_session(payload: ReplayRequest):
    """Return all actions for a session in chronological order.

    The ``speed`` parameter is validated here but only applies to real-time
    streaming via the WebSocket endpoint ``/ws/replay/{session_id}``.
    """
    if payload.speed <= 0:
        raise HTTPException(
            status_code=400,
            detail="Replay speed must be > 0.",
        )

    actions = await action_logger.get_session_actions(payload.session_id)
    return {
        "session_id": payload.session_id,
        "total": len(actions),
        "actions": actions,
    }
