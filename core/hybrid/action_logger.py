"""Action logging with durable SQLite persistence.

Design
------
``ActionLogger`` keeps an in-memory mirror of all action records so that
reads (``list_actions``, ``total_actions``) are fast and synchronous.
Every write (``record_action``, ``undo_last``, ``clear_session``) is also
flushed to SQLite, making the database the source of truth.

On process startup, call :meth:`ActionLogger.load` (e.g. from the FastAPI
``startup`` event) to reconstruct the in-memory list from the database —
including the ``undone`` flag for every action.  This is what prevents
previously undone actions from reappearing as undoable after a restart.
"""

import asyncio
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from uuid import uuid4

import aiosqlite


@dataclass
class ActionRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    type: str = ""
    description: str = ""
    domain: str = "digital"
    session_id: str = "default"
    was_guided: bool = False
    guidance_confidence: float = 0.0
    is_undoable: bool = False
    undo_instruction: Optional[str] = None
    undone: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class ActionLogger:
    """Records user actions to SQLite and maintains an in-memory mirror."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS action_log (
            id                  TEXT PRIMARY KEY,
            timestamp           TEXT    NOT NULL,
            type                TEXT    NOT NULL,
            description         TEXT    NOT NULL,
            domain              TEXT    NOT NULL,
            session_id          TEXT    NOT NULL,
            was_guided          INTEGER NOT NULL DEFAULT 0,
            guidance_confidence REAL    NOT NULL DEFAULT 0.0,
            is_undoable         INTEGER NOT NULL DEFAULT 0,
            undo_instruction    TEXT,
            undone              INTEGER NOT NULL DEFAULT 0
        )
    """

    def __init__(self, db_path: str = "data/execra.db") -> None:
        db_dir = os.path.dirname(db_path)
        if db_path != ":memory:" and db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._db_path = db_path
        self._actions: list[ActionRecord] = []

    # ------------------------------------------------------------------
    # Schema and state restoration
    # ------------------------------------------------------------------

    async def _init_db(self) -> None:
        """Ensure the ``action_log`` table exists and has the current schema.

        Creates the table if it does not exist.  For databases created by an
        earlier version of Execra (which lacked ``is_undoable``,
        ``undo_instruction``, and ``undone``), the missing columns are added
        via ``ALTER TABLE`` so that existing action history is preserved.
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(self._CREATE_TABLE)
            await db.commit()

            # Schema migration: add undo-related columns if absent.
            cursor = await db.execute("PRAGMA table_info(action_log)")
            existing = {row[1] for row in await cursor.fetchall()}
            migrations = [
                (
                    "is_undoable",
                    "ALTER TABLE action_log ADD COLUMN is_undoable INTEGER NOT NULL DEFAULT 0",
                ),
                (
                    "undo_instruction",
                    "ALTER TABLE action_log ADD COLUMN undo_instruction TEXT",
                ),
                (
                    "undone",
                    "ALTER TABLE action_log ADD COLUMN undone INTEGER NOT NULL DEFAULT 0",
                ),
            ]
            for column_name, ddl in migrations:
                if column_name not in existing:
                    await db.execute(ddl)
            await db.commit()

    async def load(self) -> None:
        """Restore the in-memory action list from the database.

        Reads all persisted rows ordered by ``timestamp`` and reconstructs
        :class:`ActionRecord` objects — including their ``undone`` state —
        so that undo history is preserved across process restarts.

        Call this once during the application startup sequence (e.g. from
        the FastAPI ``startup`` lifecycle event) before handling any
        requests.
        """
        await self._init_db()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM action_log ORDER BY timestamp ASC")
            rows = await cursor.fetchall()
        self._actions = [self._row_to_action(row) for row in rows]

    @staticmethod
    def _row_to_action(row: aiosqlite.Row) -> ActionRecord:
        return ActionRecord(
            id=row["id"],
            timestamp=row["timestamp"],
            type=row["type"],
            description=row["description"],
            domain=row["domain"],
            session_id=row["session_id"],
            was_guided=bool(row["was_guided"]),
            guidance_confidence=float(row["guidance_confidence"]),
            is_undoable=bool(row["is_undoable"]),
            undo_instruction=row["undo_instruction"],
            undone=bool(row["undone"]),
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def record_action(self, action: ActionRecord) -> ActionRecord:
        """Persist *action* to SQLite, then add it to the in-memory list.

        The database write happens before the in-memory append so that a
        failed insert never leaves the two stores out of sync.
        """
        await self._init_db()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO action_log (
                    id, timestamp, type, description, domain, session_id,
                    was_guided, guidance_confidence, is_undoable,
                    undo_instruction, undone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action.id,
                    action.timestamp,
                    action.type,
                    action.description,
                    action.domain,
                    action.session_id,
                    int(action.was_guided),
                    action.guidance_confidence,
                    int(action.is_undoable),
                    action.undo_instruction,
                    int(action.undone),
                ),
            )
            await db.commit()
        self._actions.append(action)
        return action

    def list_actions(self, limit: int = 20, offset: int = 0) -> list[ActionRecord]:
        """Return a slice of the in-memory action list."""
        return self._actions[offset : offset + limit]

    def total_actions(self) -> int:
        return len(self._actions)

    async def undo_last(self) -> Optional[ActionRecord]:
        """Mark the most recent undoable action as undone.

        Updates both the in-memory object and the ``undone`` column in
        SQLite so that undo state is durable across process restarts.

        Returns the affected :class:`ActionRecord`, or ``None`` when no
        undoable action remains.
        """
        for action in reversed(self._actions):
            if action.is_undoable and not action.undone:
                action.undone = True
                await self._init_db()
                async with aiosqlite.connect(self._db_path) as db:
                    await db.execute(
                        "UPDATE action_log SET undone = 1 WHERE id = ?",
                        (action.id,),
                    )
                    await db.commit()
                return action
        return None

    async def replay_session(
        self, session_id: Optional[str] = None, speed: float = 1.0
    ) -> AsyncIterator[ActionRecord]:
        """Yield session actions in chronological order.

        Actions whose ``undone`` flag is ``True`` are excluded so that the
        replay reflects only the committed state of the session.

        Args:
            session_id: Filter to a specific session.  Pass ``None`` to
                replay all sessions.
            speed: Replay speed multiplier — must be > 0.

        Raises:
            ValueError: If *speed* is not positive.
        """
        if speed <= 0:
            raise ValueError("Replay speed must be greater than 0")

        for action in self._actions:
            matches_session = session_id is None or action.session_id == session_id
            if matches_session and not action.undone:
                await asyncio.sleep(0)
                yield action

    def clear(self) -> None:
        """Clear the in-memory action list without touching the database.

        Intended for test isolation when the persistence layer is not under
        test (i.e. when :meth:`load` has not been called during the current
        process lifetime).
        """
        self._actions.clear()

    async def clear_session(self, session_id: str) -> None:
        """Remove all actions for *session_id* from memory and the database."""
        self._actions = [a for a in self._actions if a.session_id != session_id]
        await self._init_db()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "DELETE FROM action_log WHERE session_id = ?",
                (session_id,),
            )
            await db.commit()


action_logger = ActionLogger()
