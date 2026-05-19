from fastapi import APIRouter
from core.hybrid.guidance_dispatcher import guidance_dispatcher

router = APIRouter()


@router.get("/suppression/stats")
async def get_suppression_stats():
    """Returns alert suppression statistics."""
    stats = guidance_dispatcher.suppressor.get_suppression_stats()
    return stats