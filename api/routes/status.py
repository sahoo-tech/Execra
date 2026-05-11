import time
from fastapi import APIRouter, Request

from core.config import settings
from core.hybrid.mode_manager import mode_manager

router = APIRouter()


def _get_uptime_seconds(request: Request) -> int:
    start_time = getattr(request.app.state, "start_time", None)
    if start_time is None:
        return 0
    return max(0, int(time.time() - start_time))


@router.get("/status")
def get_status(request: Request):
    return {
        "status": "running",
        "version": request.app.version,
        "uptime_seconds": _get_uptime_seconds(request),
        "active_domain": "digital",
        "active_mode": mode_manager.current_mode,
        "perception_fps": settings.SCREEN_CAPTURE_FPS,
        "llm_backend": settings.LLM_BACKEND,
    }
