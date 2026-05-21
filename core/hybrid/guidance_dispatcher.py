import logging
from datetime import datetime, timezone
from typing import Callable
from core.hybrid.alert_suppressor import alert_suppressor
from plyer import notification

from core.models import GuidanceInstruction

logger = logging.getLogger(__name__)


class GuidanceDispatcher:
    """
    Routes GuidanceInstruction objects to registered output channels
    using the Observer pattern.
    """

    def __init__(self, enable_os_notifications: bool = False):
        """
        Initializes the dispatcher and optionally registers the default
        OS notification channel.
        """
        self._channels: list[Callable[[GuidanceInstruction], None]] = []

        if enable_os_notifications:
            self.register_channel(self._os_notification_channel)

    def register_channel(self, channel: Callable[[GuidanceInstruction], None]) -> None:
        """Registers a new output channel."""
        if channel not in self._channels:
            self._channels.append(channel)

    def dispatch(self, instruction: GuidanceInstruction, severity: str = "info") -> None:
        """Routes the instruction to all registered output channels."""
        # Check if instruction should be suppressed
        if alert_suppressor.should_suppress(instruction, severity):
            return  

        logger.info(
            f"Dispatching instruction (Step {instruction.step}/{instruction.total_steps}): "
            f"{instruction.instruction} [Confidence: {instruction.confidence:.2f}]"
        )

        for channel in self._channels:
            try:
                channel(instruction)
            except Exception as e:
                channel_name = getattr(channel, "__name__", str(channel))
                logger.error(f"Error dispatching to channel {channel_name}: {e}")

    def dispatch_error_alert(self, message: str, severity: str, confidence: float) -> None:
        """
        Convenience method to format and dispatch an error alert.
        Constructs a pseudo-GuidanceInstruction for the error.
        """
        instruction = GuidanceInstruction(
            instruction=f"[{severity.upper()}] {message}",
            confidence=confidence,
            source=["system"],
            reasoning="System error alert",
            mode="expert" if severity.lower() == "warning" else "safe",
            step=0,
            total_steps=1,
            generated_at=datetime.now(timezone.utc),
        )
        self.dispatch(instruction)

    @staticmethod
    def _os_notification_channel(instruction: GuidanceInstruction) -> None:
        """OS-level desktop notification channel using plyer."""
        try:
            notification.notify(
                title=f"Execra Guidance - Step {instruction.step}",
                message=instruction.instruction,
                app_name="Execra",
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Failed to send OS notification: {e}")
