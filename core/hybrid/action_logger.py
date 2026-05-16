from collections import deque
from datetime import datetime
from typing import Optional, Literal, AsyncIterator
from pydantic import BaseModel
import asyncio
import aiosqlite
import logging
import os

_log = logging.getLogger(__name__)


class Undoable:
    """Mixin for action types that support a human-readable undo instruction."""

    def get_undo_instruction(self) -> str:
        raise NotImplementedError


class GuidanceDispatcher:
    """Delivers undo/guidance instructions to the user interface.

    Override ``dispatch`` to integrate with a real notification layer.
    """

    async def dispatch(self, instruction: str) -> None:
        _log.info("[GuidanceDispatcher] %s", instruction)


class ActionRecord(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    type: str
    description: str
    domain: Literal["digital", "physical"]
    was_guided: bool
    guidance_confidence: float | None
    # undo / replay fields
    is_undoable: bool = False
    undo_instruction: str | None = None
    undone: bool = False
    interval: float = 0.0  # seconds since the previous action (set during replay)


class ActionLogger:
    """Records user actions to SQLite and maintains an in-memory undo stack."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS action_log (
            id                 TEXT PRIMARY KEY,
            session_id         TEXT,
            timestamp          TEXT,
            type               TEXT,
            description        TEXT,
            domain             TEXT,
            was_guided         INTEGER,
            guidance_confidence REAL,
            is_undoable        INTEGER DEFAULT 0,
            undo_instruction   TEXT,
            undone             INTEGER DEFAULT 0
        )
    """

    def __init__(self, db_path: str = "data/execra.db"):
        """Initialize logger with database path and empty undo stack (max 50)."""
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._stack: deque[ActionRecord] = deque(maxlen=50)
        # Tracks IDs of actions that have already been undone (safe double-undo).
        self._undone_ids: set[str] = set()

    async def _init_db(self) -> None:
        """Create the action_log table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(self._CREATE_TABLE)
            await db.commit()

    @staticmethod
    def _row_to_action(row: tuple) -> "ActionRecord":
        """Convert a SQLite row tuple to an ActionRecord."""
        return ActionRecord(
            id=row[0],
            session_id=row[1],
            timestamp=datetime.fromisoformat(row[2]),
            type=row[3],
            description=row[4],
            domain=row[5],
            was_guided=bool(row[6]),
            guidance_confidence=row[7],
            is_undoable=bool(row[8]) if len(row) > 8 else False,
            undo_instruction=row[9] if len(row) > 9 else None,
            undone=bool(row[10]) if len(row) > 10 else False,
        )

    async def log_action(self, action: ActionRecord) -> None:
        """Save action to SQLite and append to in-memory undo stack."""
        await self._init_db()

        self._stack.append(action)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO action_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    action.id,
                    action.session_id,
                    action.timestamp.isoformat(),
                    action.type,
                    action.description,
                    action.domain,
                    int(action.was_guided),
                    action.guidance_confidence,
                    int(action.is_undoable),
                    action.undo_instruction,
                    int(action.undone),
                ),
            )
            await db.commit()

    def undo_last(
        self, dispatcher: Optional[GuidanceDispatcher] = None
    ) -> Optional[ActionRecord]:
        """Find and mark the last undoable action as undone.

        Walks the in-memory stack backward to locate the most recent action
        where ``is_undoable=True`` and whose ID is not already in
        ``_undone_ids``.  The action ID is added to ``_undone_ids`` so that
        a second call (double-undo) safely returns ``None`` without affecting
        any other action.

        If *dispatcher* is provided and the action carries an
        ``undo_instruction``, the instruction is dispatched asynchronously
        without blocking the caller.
        """
        for i in range(len(self._stack) - 1, -1, -1):
            action = self._stack[i]
            if action.is_undoable and action.id not in self._undone_ids:
                self._undone_ids.add(action.id)

                if dispatcher and action.undo_instruction:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(
                                dispatcher.dispatch(action.undo_instruction)
                            )
                    except RuntimeError:
                        pass

                return action

        return None

    async def replay_session(
        self, session_id: str, speed: float = 1.0
    ) -> AsyncIterator[ActionRecord]:
        """Async generator that yields session actions in chronological order.

        Inserts ``asyncio.sleep(interval / speed)`` between successive actions
        to preserve original timing at the requested speed factor (> 1 = faster,
        < 1 = slower).  The ``interval`` field of each yielded action is set to
        the elapsed seconds since the previous action.

        Raises ``ValueError`` if *speed* is not > 0.
        Replay is read-only and does not modify the action history.
        """
        if speed <= 0:
            raise ValueError(f"Replay speed must be > 0, got {speed!r}")

        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM action_log WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            )
            rows = await cursor.fetchall()

        prev_time: Optional[datetime] = None
        for row in rows:
            action = self._row_to_action(row)
            if prev_time is not None:
                interval = max((action.timestamp - prev_time).total_seconds(), 0.0)
                action = action.model_copy(update={"interval": interval})
                await asyncio.sleep(interval / speed)
            prev_time = action.timestamp
            yield action

    async def get_session_actions(self, session_id: str) -> list[ActionRecord]:
        """Fetch all actions for a session in chronological order (no timing)."""
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM action_log WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            )
            rows = await cursor.fetchall()
        return [self._row_to_action(row) for row in rows]

    async def get_history(self, limit: int = 20, offset: int = 0) -> list[ActionRecord]:
        """Fetch paginated action history from SQLite, newest first."""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM action_log ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            rows = await cursor.fetchall()

        return [self._row_to_action(row) for row in rows]

    async def clear_session(self, session_id: str) -> None:
        """Delete all actions for the session from SQLite and clear in-memory state."""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM action_log WHERE session_id = ?", (session_id,)
            )
            await db.commit()

        self._stack.clear()
        self._undone_ids.clear()


action_logger = ActionLogger()
