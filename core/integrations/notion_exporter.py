import logging
from typing import List
from notion_client import Client
from core.hybrid.action_logger import ActionRecord

logger = logging.getLogger(__name__)

class NotionExporter:
    def __init__(self, api_key: str):
        self.client = Client(auth=api_key)

    def _create_table_row(self, cells: List[str]) -> dict:
        """Create a Notion table row block from a list of cell strings."""
        return {
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": {"content": str(cell)[:2000]}}] for cell in cells
                ]
            }
        }

    def export_session(self, session_id: str, page_id: str, actions: List[ActionRecord]) -> str:
        """
        Export a session's actions to a new Notion page.
        Returns the URL of the created page.
        """
        page_properties = {
            "title": [
                {
                    "text": {
                        "content": f"Execra Session: {session_id}"
                    }
                }
            ]
        }

        # Header row
        headers = ["Timestamp", "Action Type", "Description", "Domain", "Guided", "Confidence"]
        
        # Notion API limits block children to 100 elements. 
        # A table block can have max 100 rows. We reserve 1 for header.
        CHUNK_SIZE = 99 
        
        blocks = []
        for i in range(0, len(actions), CHUNK_SIZE):
            chunk = actions[i:i + CHUNK_SIZE]
            
            table_children = [self._create_table_row(headers)]
            for action in chunk:
                confidence_str = f"{action.guidance_confidence:.2f}" if action.guidance_confidence is not None else "N/A"
                row_data = [
                    action.timestamp.isoformat(),
                    action.type,
                    action.description,
                    action.domain,
                    "Yes" if action.was_guided else "No",
                    confidence_str
                ]
                table_children.append(self._create_table_row(row_data))
                
            table_block = {
                "object": "block",
                "type": "table",
                "table": {
                    "table_width": 6,
                    "has_column_header": True,
                    "has_row_header": False,
                    "children": table_children
                }
            }
            blocks.append(table_block)

        try:
            response = self.client.pages.create(
                parent={"page_id": page_id},
                properties=page_properties,
                children=blocks
            )
            new_page = dict(response) if isinstance(response, dict) else getattr(response, "__dict__", {})
            page_url = new_page.get('url', "")
            logger.info(f"Successfully exported session {session_id} to Notion page: {page_url}")
            return page_url
        except Exception as e:
            logger.error(f"Failed to export session {session_id} to Notion: {e}")
            raise
