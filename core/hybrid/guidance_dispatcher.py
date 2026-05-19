"""
Guidance Dispatcher — delivers instructions to the user with alert suppression.
"""

import logging
from core.hybrid.alert_suppressor import AlertSuppressor
from core.config import settings

logger = logging.getLogger(__name__)


class GuidanceDispatcher:
    """Dispatches guidance instructions with alert suppression."""

    def __init__(self):
        self.suppressor = AlertSuppressor(
            cooldown_map={
                "info": settings.ALERT_COOLDOWN_INFO,
                "warning": settings.ALERT_COOLDOWN_WARNING,
                "critical": 0,
            }
        )

    def dispatch(self, instruction) -> bool:
        """
        Dispatch a guidance instruction.
        Returns True if dispatched, False if suppressed.
        """
        if self.suppressor.should_suppress(instruction):
            logger.debug(f"Instruction suppressed: {instruction.instruction}")
            return False

        logger.info(
            f"[{getattr(instruction, 'severity', 'info').upper()}] "
            f"Dispatching: {instruction.instruction} (mode={instruction.mode})"
        )
        return True


guidance_dispatcher = GuidanceDispatcher()