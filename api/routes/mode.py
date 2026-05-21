from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.hybrid.mode_manager import mode_manager


router = APIRouter()

class ModeRequest(BaseModel):
    mode: str

# Returns current mode with description
@router.get("/mode")
async def get_mode():
    return mode_manager.get_current_mode()

# Switches mode based on user input
@router.put("/mode")
async def switch_mode(request: ModeRequest):
    try:
        mode_manager.switch_mode(request.mode)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid mode value")
    
    result = mode_manager.get_current_mode()
    return {
        "mode": result["mode"],
        "message": result["description"]
    }