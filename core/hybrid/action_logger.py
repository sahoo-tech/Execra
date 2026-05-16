from collections import deque
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel
import aiosqlite
import os


class ActionRecord(BaseModel):
    id: str
    session_id: str # session_id was missing in the data model, added it here
    timestamp: datetime
    type: str
    description: str
    domain: Literal["digital", "physical"]
    was_guided: bool
    guidance_confidence: float | None

class ActionLogger:
    """Records user actions to SQLite and maintains an in-memory undo stack."""

    def __init__(self, db_path: str = "data/execra.db"):
        """Initialize logger with database path and empty undo stack (max 50)."""
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._stack = deque(maxlen=50)

    async def _init_db(self):
        """Create the action_log table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS action_log (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    type TEXT,
                    description TEXT,
                    domain TEXT,
                    was_guided INTEGER,
                    guidance_confidence REAL
                )
            """)
            await db.commit()

    async def log_action(self, action: ActionRecord) -> None:
        """Save action to SQLite and append to in-memory undo stack."""
        await self._init_db()  # ensure table exists

        # Add to in-memory deque
        self._stack.append(action)

        # Save to SQLite
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO action_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action.id,
                action.session_id,
                action.timestamp.isoformat(),
                action.type,
                action.description,
                action.domain,
                int(action.was_guided),
                action.guidance_confidence
            ))
            await db.commit()
    
    def undo_last(self) -> Optional[ActionRecord]:
        """Pop and return the last action from the undo stack. Returns None if empty."""
        if not self._stack:
            return None
        return self._stack.pop()
    
    async def get_history(self, limit: int = 20, offset: int = 0) -> list[ActionRecord]:
        """Fetch paginated action history from SQLite, newest first."""
        await self._init_db()  # ensure table exists

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM action_log
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = await cursor.fetchall()

        return [
            ActionRecord(
                id=row[0],
                session_id=row[1],
                timestamp=datetime.fromisoformat(row[2]),
                type=row[3],
                description=row[4],
                domain=row[5],
                was_guided=bool(row[6]),
                guidance_confidence=row[7]
            )
            for row in rows
        ]
    async def clear_session(self, session_id: str) -> None:
        """Delete all actions for the session from SQLite and clear the in-memory stack."""
        await self._init_db()  # ensure table exists

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM action_log WHERE session_id = ?",
                (session_id,)
            )
            await db.commit()

        self._stack.clear()

action_logger = ActionLogger()