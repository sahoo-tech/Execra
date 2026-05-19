"""
Alert Suppression System for Execra.
Deduplicates and throttles repeated guidance instructions based on configurable cooldown rules.
"""

import time
import logging
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.intelligence.trust_scorer import GuidanceInstruction

logger = logging.getLogger(__name__)

MAX_SUPPRESSION_ENTRIES = 500


class AlertSuppressor:
    """
    Intelligently deduplicates and throttles repeated guidance instructions
    based on configurable cooldown rules per severity level.
    """

    def __init__(self, cooldown_map: dict[str, int] = None):
        """
        Initialize with cooldown map.
        Default: info=60s, warning=30s, critical=0 (never suppressed)
        """
        self.cooldown_map = cooldown_map or {
            "info": 60,
            "warning": 30,
            "critical": 0,
        }
        # OrderedDict for LRU eviction: key -> (expiry_timestamp, severity)
        self._suppression_map: OrderedDict[int, tuple[float, str]] = OrderedDict()
        self._total_suppressed = 0
        self._suppressed_by_severity: dict[str, int] = {}

    def _make_key(self, instruction) -> int:
        """Generate hash key from instruction text + mode."""
        return hash(instruction.instruction + instruction.mode)

    def should_suppress(self, instruction) -> bool:
        """
        Returns True if an identical instruction was delivered within the cooldown window.
        Critical severity is never suppressed.
        """
        severity = getattr(instruction, "severity", "info").lower()

        # Critical instructions are never suppressed
        cooldown = self.cooldown_map.get(severity, 60)
        if cooldown == 0:
            return False

        key = self._make_key(instruction)
        now = time.time()

        if key in self._suppression_map:
            expiry, _ = self._suppression_map[key]
            if now < expiry:
                # Still within cooldown — suppress it
                self._total_suppressed += 1
                self._suppressed_by_severity[severity] = (
                    self._suppressed_by_severity.get(severity, 0) + 1
                )
                logger.debug(
                    f"Suppressed instruction: '{instruction.instruction}' "
                    f"(severity={severity}, expires in {expiry - now:.1f}s)"
                )
                return True
            else:
                # Cooldown expired — remove stale entry
                del self._suppression_map[key]

        # Not suppressed — record it with expiry
        self._suppression_map[key] = (now + cooldown, severity)

        # LRU eviction if over max entries
        while len(self._suppression_map) > MAX_SUPPRESSION_ENTRIES:
            self._suppression_map.popitem(last=False)  # Remove oldest

        return False

    def reset(self, instruction_text: str) -> None:
        """Manually clear the suppression record for a specific instruction text."""
        keys_to_delete = [
            k for k in self._suppression_map
            if str(k) == str(hash(instruction_text + "passive"))
            or str(k) == str(hash(instruction_text + "active"))
            or str(k) == str(hash(instruction_text + "mixed"))
        ]
        for k in keys_to_delete:
            del self._suppression_map[k]

    def get_suppression_stats(self) -> dict:
        """Returns suppression statistics."""
        return {
            "total_suppressed": self._total_suppressed,
            "by_severity": dict(self._suppressed_by_severity),
        }