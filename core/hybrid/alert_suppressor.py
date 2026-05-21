import logging
import time
from collections import OrderedDict
from core.models import GuidanceInstruction
from core.config import settings

logger = logging.getLogger(__name__)

class AlertSuppressor:

    def __init__(self, cooldown_map: dict[str, int]):
        self.cooldown_map = cooldown_map
        self._suppression_map: OrderedDict = OrderedDict()
        self.MAX_SIZE = 500
        self._stats = {
            "total_suppressed": 0,
            "by_severity": {}
        }

    def should_suppress(self, instruction: GuidanceInstruction, severity: str) -> bool:
        """Return True if the same instruction was sent within the cooldown window."""

        if severity == "critical":
            return False

        # Compute unique key for this instruction
        key = hash(instruction.instruction + instruction.mode)
        now = time.time()

        # Check if instruction is still in cooldown
        if key in self._suppression_map:
            expiry = self._suppression_map[key]
            if now < expiry:
                self._suppression_map.move_to_end(key)

                # Update stats
                self._stats["total_suppressed"] += 1
                self._stats["by_severity"][severity] = self._stats["by_severity"].get(severity, 0) + 1

                # Log suppressed instruction
                logger.debug(f"Suppressed instruction: {instruction.instruction}")
                return True

        cooldown = self.cooldown_map.get(severity, 0)
        self._suppression_map[key] = now + cooldown

        # LRU eviction if map exceeds max size
        if len(self._suppression_map) > self.MAX_SIZE:
            self._suppression_map.popitem(last=False)

        return False
    
    def reset(self, instruction_text: str) -> None:
        """Manually clear the suppression record for a specific instruction."""

        for mode in ["safe", "expert"]:
            key = hash(instruction_text + mode)
            if key in self._suppression_map:
                del self._suppression_map[key]

    def get_suppression_stats(self) -> dict:
        """Return stats about suppressed instructions."""
        return self._stats
    

# Shared instance — initialized with default cooldowns from config

alert_suppressor = AlertSuppressor(cooldown_map={
    "info": settings.ALERT_COOLDOWN_INFO,
    "warning": settings.ALERT_COOLDOWN_WARNING,
    "critical": 0
})