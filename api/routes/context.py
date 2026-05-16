from datetime import datetime
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.hybrid.action_logger import action_logger


router = APIRouter()


class ErrorRecord(BaseModel):
    step: int
    error: str
    resolved: bool


class SessionContext(BaseModel):
    session_id: str
    task_type: str
    current_step: int
    total_steps: int
    step_description: str
    error_history: list[ErrorRecord]
    domain: Literal["digital", "physical", "hybrid"]
    started_at: datetime

# In memory placeholder until SessionContext is wired to SQLite
_current_context: SessionContext | None = None

@router.get("/context")
async def get_context():
    if _current_context is None:
        raise HTTPException(
            status_code=404,
            detail="No active session context found. Start Execra first."
        )
    return _current_context

@router.delete("/context")
async def clear_context():
    global _current_context

    if _current_context is not None:
        await action_logger.clear_session(_current_context.session_id)

    _current_context = None

    return {"message": "Session context cleared."}
