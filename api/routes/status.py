from fastapi import APIRouter
import time
from core.config import settings

router = APIRouter()

start_time = time.time()

@router.get('/status')
async def get_status():
    uptime_seconds = int(time.time() - start_time)

    return {
        "status": "running",
        "version": "0.1.0",
        "uptime_seconds": uptime_seconds,
        "active_domain": "digital",
        "active_mode": "passivesta",
        "perception_fps": settings.SCREEN_CAPTURE_FPS,
        "llm_backend": settings.LLM_BACKEND
        } 
    