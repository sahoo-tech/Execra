from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.hybrid.action_logger import action_logger
from core.integrations.notion_exporter import NotionExporter
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ExportSessionRequest(BaseModel):
    session_id: str

@router.post("/session/export/notion")
async def export_session_to_notion(request: ExportSessionRequest):
    if not settings.NOTION_API_KEY or not settings.NOTION_PARENT_PAGE_ID:
        raise HTTPException(status_code=500, detail="Notion configuration is missing (NOTION_API_KEY or NOTION_PARENT_PAGE_ID)")
        
    actions = await action_logger.get_actions_by_session(request.session_id)
    if not actions:
        raise HTTPException(status_code=404, detail=f"No actions found for session_id: {request.session_id}")
        
    exporter = NotionExporter(settings.NOTION_API_KEY)
    try:
        url = exporter.export_session(request.session_id, settings.NOTION_PARENT_PAGE_ID, actions)
        return {"message": "Session exported successfully to Notion", "url": url}
    except Exception as e:
        logger.error(f"Failed to export session to Notion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export session: {str(e)}")
