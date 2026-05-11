from dataclasses import dataclass, field
from typing import Callable, Dict, List

VALID_MODES = ("passive", "active", "mixed")

MODE_DESCRIPTIONS = {
    "passive": "Auto-observe and guide without prompts",
    "active": "Respond to explicit user questions",
    "mixed": "Run passive guidance and active Q&A",
}


@dataclass
class ModeManager:
    current_mode: str = "passive"
    _observers: List[Callable[[str], None]] = field(default_factory=list)

    def switch_mode(self, mode: str) -> None:
        if mode not in VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")
        if mode == self.current_mode:
            return
        self.current_mode = mode
        self._notify_observers()

    def get_current_mode(self) -> Dict[str, str]:
        return {
            "mode": self.current_mode,
            "description": MODE_DESCRIPTIONS[self.current_mode],
        }

    def on_mode_change(self, callback: Callable[[str], None]) -> None:
        self._observers.append(callback)

    def _notify_observers(self) -> None:
        for callback in self._observers:
            callback(self.current_mode)


mode_manager = ModeManager()
