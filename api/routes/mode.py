from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.hybrid.mode_manager import mode_manager

router = APIRouter()


class ModeUpdate(BaseModel):
    mode: str


class ModeResponse(BaseModel):
    mode: str
    description: str


@router.get("/mode", response_model=ModeResponse)
def get_mode():
    return mode_manager.get_current_mode()


@router.put("/mode", response_model=ModeResponse)
def set_mode(payload: ModeUpdate):
    try:
        mode_manager.switch_mode(payload.mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return mode_manager.get_current_mode()
