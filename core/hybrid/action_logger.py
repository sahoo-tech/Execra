import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator, Optional
from uuid import uuid4


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


class ActionLogger:
    def __init__(self):
        self._actions: list[ActionRecord] = []

    def record_action(self, action: ActionRecord) -> ActionRecord:
        self._actions.append(action)
        return action

    def list_actions(self, limit: int = 20, offset: int = 0) -> list[ActionRecord]:
        return self._actions[offset : offset + limit]

    def total_actions(self) -> int:
        return len(self._actions)

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


action_logger = ActionLogger()
