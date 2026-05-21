from collections import deque
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel
import aiosqlite
import os
import uuid
from core.security.crypto import encrypt,decrypt
import logging

logger = logging.getLogger(__name__)

@dataclass
class ActionRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
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


        self.db_path = db_path
        self._stack = deque(maxlen=50)
        self.on_log_callbacks = []

    def register_callback(self, cb) -> None:
        """Register a callback to be executed when an action is logged."""
        if cb not in self.on_log_callbacks:
            self.on_log_callbacks.append(cb)

    def unregister_callback(self, cb) -> None:
        """Unregister a callback."""
        if cb in self.on_log_callbacks:
            self.on_log_callbacks.remove(cb)

    def record_action(self, action: ActionRecord) -> ActionRecord:
        self._actions.append(action)
        return action

    async def log_action(self, action: ActionRecord) -> None:
        """Save action to SQLite, append to stack, and trigger callbacks."""
        await self._init_db()  # ensure table exists

    def total_actions(self) -> int:
        return len(self._actions)

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

        # Trigger callbacks
        for cb in list(self.on_log_callbacks):
            try:
                import inspect
                if inspect.iscoroutinefunction(cb):
                    await cb(action)
                else:
                    cb(action)
            except Exception as e:
                logger.error(f"Error in action log callback: {e}")
    
    def undo_last(self) -> Optional[ActionRecord]:
        for action in reversed(self._actions):
            if action.is_undoable and not action.undone:
                action.undone = True
                return action
        return None

    async def replay_session(
        self, session_id: Optional[str] = None, speed: float = 1.0
    ) -> AsyncIterator[ActionRecord]:
        if speed <= 0:
            raise ValueError("Replay speed must be greater than 0")

        for action in self._actions:
            if session_id is None or action.session_id == session_id:
                await asyncio.sleep(0)
                yield action

    def clear(self) -> None:
        self._actions.clear()

    async def clear_session(self, session_id: str) -> None:
        self._actions = [a for a in self._actions if a.session_id != session_id]


    async def log_error(self, session_id: str, step: int, error: str) -> None:
        """Encrypt and save an error to the error_history table."""
        encrypted_error = encrypt(error)
        error_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS error_history (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    step INTEGER,
                    error TEXT
                )
            """)
            await db.execute("""
                INSERT INTO error_history (id, session_id, step, error)
                VALUES (?, ?, ?, ?)
            """, (error_id, session_id, step, encrypted_error))
            await db.commit()

    async def get_errors(self, session_id: str) -> list[Dict[str, Any]]:
        """Fetch and decrypt all errors for a session."""
        errors = []
        async with aiosqlite.connect(self.db_path) as db:
            # Check if the table exists yet
            async with db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='error_history'"
            ) as cursor:
                if not await cursor.fetchone():
                    return []

            async with db.execute(
                "SELECT id, session_id, step, error FROM error_history WHERE session_id = ? ORDER BY step",
                (session_id,)
            ) as cursor:
                async for row in cursor:
                    encrypted_error = row[3]
                    decrypted_error = decrypt(encrypted_error) if encrypted_error else ""
                    errors.append({
                        "id": row[0],
                        "session_id": row[1],
                        "step": row[2],
                        "error": decrypted_error
                    })
        return errors

action_logger = ActionLogger()
