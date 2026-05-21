from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.hybrid.action_logger import ActionRecord, action_logger
from fastapi import APIRouter, HTTPException
from core.hybrid.action_logger import action_logger, ActionRecord

router = APIRouter()


class ActionCreate(BaseModel):
    type: str
    description: str
    domain: str = "digital"
    session_id: str = "default"
    was_guided: bool = False
    guidance_confidence: float = 0.0
    is_undoable: bool = False
    undo_instruction: Optional[str] = None


class ReplayRequest(BaseModel):
    session_id: Optional[str] = None
    speed: float = 1.0


@router.get("/actions")
def get_actions(limit: int = Query(20, ge=1), offset: int = Query(0, ge=0)):
    actions = action_logger.list_actions(limit=limit, offset=offset)
    return {
        "total": action_logger.total_actions(),
        "actions": [action.to_dict() for action in actions],
    }

@router.post("/actions")
async def create_action(action: ActionRecord):
    await action_logger.log_action(action)
    return {
        "message": "Action logged successfully.",
        "action": action
    }

@router.post("/actions/undo")
async def undo_last_action():
    undone = action_logger.undo_last()

@router.post("/actions")
def create_action(payload: ActionCreate):
    action = ActionRecord(**payload.dict())
    action_logger.record_action(action)
    return {"action": action.to_dict()}


@router.post("/actions/undo")
def undo_last_action():
    action = action_logger.undo_last()
    if action is None:
        raise HTTPException(status_code=409, detail="Nothing in the undo stack")

    return {
        "message": "Last action undone successfully.",
        "action_undone": action.to_dict(),
    }


@router.post("/actions/replay")
async def replay_actions(payload: ReplayRequest):
    try:
        actions = [
            action.to_dict()
            async for action in action_logger.replay_session(
                session_id=payload.session_id,
                speed=payload.speed,
            )
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"total": len(actions), "actions": actions}
