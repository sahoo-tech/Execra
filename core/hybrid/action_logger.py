"""Action logging with durable SQLite persistence.

Design
------
``ActionLogger`` keeps two in-memory mirrors of the persisted action log:

* ``_stack`` — a ``deque(maxlen=50)`` of the most recent actions, used by
  the upstream undo and callback infrastructure.
* ``_actions`` — a plain list of *all* actions, used by replay and the
  paginated list API.

Every write (``log_action``, ``undo_last``, ``clear_session``) is flushed
to SQLite first so the database is always the source of truth.

On process startup, call :meth:`ActionLogger.load` (e.g. from the FastAPI
``startup`` event) to reconstruct both in-memory structures from the
database — including the ``undone`` flag for every action — so that undo
state is preserved across process restarts.
"""

import asyncio
import inspect
import logging
import os
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Literal, Optional
from uuid import uuid4

import aiosqlite
from pydantic import BaseModel, Field

from core.security.crypto import decrypt, encrypt

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class ActionRecord(BaseModel):
    """A single user action captured by Execra.

    The ``is_undoable``, ``undo_instruction``, and ``undone`` fields are
    optional with safe defaults so that existing code that constructs
    ``ActionRecord`` without them continues to work unchanged.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str = "default"
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    type: str = ""
    description: str = ""
    domain: Literal["digital", "physical"] = "digital"
    was_guided: bool = False
    guidance_confidence: float | None = None
    # Undo / replay fields
    is_undoable: bool = False
    undo_instruction: Optional[str] = None
    undone: bool = False

    def to_dict(self) -> dict:
        return self.model_dump()


# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------


class ActionLogger:
    """Records user actions to SQLite and maintains in-memory mirrors."""

    _CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS action_log (
            id                  TEXT PRIMARY KEY,
            session_id          TEXT,
            timestamp           TEXT,
            type                TEXT,
            description         TEXT,
            domain              TEXT,
            was_guided          INTEGER,
            guidance_confidence REAL,
            is_undoable         INTEGER NOT NULL DEFAULT 0,
            undo_instruction    TEXT,
            undone              INTEGER NOT NULL DEFAULT 0
        )
    """

    def __init__(self, db_path: str = "data/execra.db") -> None:
        if db_path != ":memory:":
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        # Deque kept for upstream compatibility (undo stack, callback tests).
        self._stack: deque[ActionRecord] = deque(maxlen=50)
        # Full list used by replay and list_actions().
        self._actions: list[ActionRecord] = []
        self.on_log_callbacks: list = []

    # ------------------------------------------------------------------
    # Observer callbacks
    # ------------------------------------------------------------------

    def register_callback(self, cb) -> None:
        """Register a callback to be invoked when an action is logged."""
        if cb not in self.on_log_callbacks:
            self.on_log_callbacks.append(cb)

    def unregister_callback(self, cb) -> None:
        """Unregister a previously registered callback."""
        if cb in self.on_log_callbacks:
            self.on_log_callbacks.remove(cb)

    # ------------------------------------------------------------------
    # Schema and state restoration
    # ------------------------------------------------------------------

    async def _init_db(self) -> None:
        """Ensure the ``action_log`` table exists with the current schema.

        Creates the table if absent.  For databases created by an earlier
        version of Execra (which lacked the undo-related columns), the
        missing columns are added via ``ALTER TABLE`` so that existing
        action history is preserved without data loss.
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(self._CREATE_TABLE)
            await db.commit()

            # Schema migration: add undo columns if absent.
            cursor = await db.execute("PRAGMA table_info(action_log)")
            existing = {row[1] for row in await cursor.fetchall()}
            migrations = [
                (
                    "is_undoable",
                    "ALTER TABLE action_log ADD COLUMN"
                    " is_undoable INTEGER NOT NULL DEFAULT 0",
                ),
                (
                    "undo_instruction",
                    "ALTER TABLE action_log ADD COLUMN undo_instruction TEXT",
                ),
                (
                    "undone",
                    "ALTER TABLE action_log ADD COLUMN"
                    " undone INTEGER NOT NULL DEFAULT 0",
                ),
            ]
            for column_name, ddl in migrations:
                if column_name not in existing:
                    await db.execute(ddl)
            await db.commit()

    async def load(self) -> None:
        """Restore in-memory state from the database.

        Reads all persisted rows ordered by ``timestamp`` and reconstructs
        :class:`ActionRecord` objects — including their ``undone`` state —
        so that undo history is preserved across process restarts.

        Populates both ``_actions`` (full history) and ``_stack`` (most
        recent 50).  Call once during the application startup sequence
        before any requests are served.
        """
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM action_log ORDER BY timestamp ASC"
            )
            rows = await cursor.fetchall()

        self._actions = [self._row_to_action(row) for row in rows]
        self._stack = deque(self._actions, maxlen=50)

    @staticmethod
    def _row_to_action(row: aiosqlite.Row) -> ActionRecord:
        return ActionRecord(
            id=row["id"],
            session_id=row["session_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            type=row["type"],
            description=row["description"],
            domain=row["domain"],
            was_guided=bool(row["was_guided"]),
            guidance_confidence=row["guidance_confidence"],
            is_undoable=bool(row["is_undoable"]),
            undo_instruction=row["undo_instruction"],
            undone=bool(row["undone"]),
        )

    # ------------------------------------------------------------------
    # Public write interface
    # ------------------------------------------------------------------

    async def log_action(self, action: ActionRecord) -> None:
        """Persist *action* to SQLite, update in-memory state, fire callbacks.

        The database write happens before the in-memory update so that a
        failed insert never leaves the two stores inconsistent.
        """
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO action_log (
                    id, session_id, timestamp, type, description, domain,
                    was_guided, guidance_confidence, is_undoable,
                    undo_instruction, undone
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
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

        self._stack.append(action)
        self._actions.append(action)

        for cb in list(self.on_log_callbacks):
            try:
                if inspect.iscoroutinefunction(cb):
                    await cb(action)
                else:
                    cb(action)
            except Exception as exc:
                logger.error("Error in action log callback: %s", exc)

    async def undo_last(self) -> Optional[ActionRecord]:
        """Mark the most recent undoable action as undone.

        Updates both the in-memory ``ActionRecord`` object and the
        ``undone`` column in SQLite so that undo state is durable across
        process restarts.  Returns the affected record, or ``None`` when
        no undoable action remains.
        """
        for action in reversed(self._actions):
            if action.is_undoable and not action.undone:
                action.undone = True
                await self._init_db()
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        "UPDATE action_log SET undone = 1 WHERE id = ?",
                        (action.id,),
                    )
                    await db.commit()
                return action
        return None

    # ------------------------------------------------------------------
    # Public read interface
    # ------------------------------------------------------------------

    def list_actions(self, limit: int = 20, offset: int = 0) -> list[ActionRecord]:
        """Return a slice of the in-memory action list (all sessions)."""
        return self._actions[offset : offset + limit]

    def total_actions(self) -> int:
        return len(self._actions)

    async def get_history(
        self, limit: int = 20, offset: int = 0
    ) -> list[ActionRecord]:
        """Fetch paginated action history from SQLite, newest first."""
        await self._init_db()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM action_log
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = await cursor.fetchall()

        return [self._row_to_action(row) for row in rows]

    async def replay_session(
        self, session_id: Optional[str] = None, speed: float = 1.0
    ) -> AsyncIterator[ActionRecord]:
        """Yield session actions in chronological order.

        Actions whose ``undone`` flag is ``True`` are excluded so that the
        replay reflects only the committed state of the session.

        Args:
            session_id: Filter to a specific session.  ``None`` replays all.
            speed: Replay speed multiplier — must be > 0.

        Raises:
            ValueError: If *speed* is not positive.
        """
        if speed <= 0:
            raise ValueError("Replay speed must be greater than 0")

        for action in self._actions:
            matches = session_id is None or action.session_id == session_id
            if matches and not action.undone:
                await asyncio.sleep(0)
                yield action

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Clear in-memory state without touching the database.

        Intended for test isolation when the persistence layer is not
        under test (i.e. when ``load()`` has not been called).
        """
        self._actions.clear()
        self._stack.clear()

    async def clear_session(self, session_id: str) -> None:
        """Remove all actions for *session_id* from memory and the database."""
        self._actions = [a for a in self._actions if a.session_id != session_id]
        self._stack = deque(
            (a for a in self._stack if a.session_id != session_id),
            maxlen=50,
        )
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM action_log WHERE session_id = ?",
                (session_id,),
            )
            await db.commit()

    # ------------------------------------------------------------------
    # Encrypted error history (upstream feature)
    # ------------------------------------------------------------------

    async def log_error(self, session_id: str, step: int, error: str) -> None:
        """Encrypt and save an error to the ``error_history`` table."""
        encrypted_error = encrypt(error)
        error_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS error_history (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    step INTEGER,
                    error TEXT
                )
                """
            )
            await db.execute(
                """
                INSERT INTO error_history (id, session_id, step, error)
                VALUES (?, ?, ?, ?)
                """,
                (error_id, session_id, step, encrypted_error),
            )
            await db.commit()

    async def get_errors(self, session_id: str) -> list[Dict[str, Any]]:
        """Fetch and decrypt all errors for a session."""
        errors: list[Dict[str, Any]] = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
                " AND name='error_history'"
            ) as cursor:
                if not await cursor.fetchone():
                    return []

            async with db.execute(
                """
                SELECT id, session_id, step, error
                FROM error_history
                WHERE session_id = ?
                ORDER BY step
                """,
                (session_id,),
            ) as cursor:
                async for row in cursor:
                    decrypted = decrypt(row[3]) if row[3] else ""
                    errors.append(
                        {
                            "id": row[0],
                            "session_id": row[1],
                            "step": row[2],
                            "error": decrypted,
                        }
                    )
        return errors


action_logger = ActionLogger()
