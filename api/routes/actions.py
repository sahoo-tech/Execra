from fastapi import APIRouter, HTTPException
from core.hybrid.action_logger import action_logger

router = APIRouter()

@router.get("/actions")
async def get_actions(limit: int = 20, offset: int = 0):
    actions = await action_logger.get_history(limit=limit, offset=offset)
    return {
        "total": len(actions),
        "actions": actions
    }

@router.post("/actions/undo")
async def undo_last_action():
    undone = action_logger.undo_last()

    if undone is None:
        raise HTTPException(
            status_code=409,
            detail="Nothing to undo. Action log is empty."
        )

    return {
        "message": "Last action undone successfully.",
        "action_undone": {
            "id": undone.id,
            "description": undone.description
        }

    }