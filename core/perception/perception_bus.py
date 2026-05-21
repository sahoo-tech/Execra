import asyncio
import logging
from typing import Optional

from core.perception.screen_capture import ScreenCapture
from core.perception.camera_feed import CameraFeed

logger = logging.getLogger(__name__)


class PerceptionBus:
    """
    The Perception Bus is the single entry point that receives frames from screen capture
    and camera feed and routes them to the correct processing engine based on the active domain.
    """

    def __init__(
        self,
        domain: str,
        screen_capture: Optional[ScreenCapture] = None,
        camera_feed: Optional[CameraFeed] = None,
    ):
        """
        Initialize the Perception Bus.

        Args:
            domain: The active domain ('digital', 'physical', or 'hybrid').
            screen_capture: Optional customized ScreenCapture instance.
            camera_feed: Optional customized CameraFeed instance.

        Raises:
            ValueError: If the active domain is not 'digital', 'physical', or 'hybrid'.
        """
        valid_domains = {"digital", "physical", "hybrid"}
        if domain not in valid_domains:
            raise ValueError(
                f"Invalid domain: '{domain}'. Must be one of {valid_domains}"
            )

        self.domain = domain
        self.screen_capture = screen_capture or ScreenCapture()
        self.camera_feed = camera_feed or CameraFeed()

        # Output queues
        self.screen_queue: asyncio.Queue = asyncio.Queue()
        self.camera_queue: asyncio.Queue = asyncio.Queue()

        self._running = False

    async def start(self) -> None:
        """
        Start the appropriate capture sources based on the active domain.
        - digital -> screen only
        - physical -> camera only
        - hybrid -> both capture sources concurrently
        """
        if self._running:
            logger.warning("PerceptionBus is already running.")
            return

        self._running = True
        loop = asyncio.get_running_loop()

        logger.info("Starting PerceptionBus for domain: %s", self.domain)

        if self.domain == "digital":
            self.screen_capture.start_capture_loop(self.screen_queue)
        elif self.domain == "physical":
            self.camera_feed.start_feed_loop(self.camera_queue, loop)
        elif self.domain == "hybrid":
            # Concurrently run both capture loops using asyncio.gather()
            async def start_screen():
                self.screen_capture.start_capture_loop(self.screen_queue)

            async def start_camera():
                self.camera_feed.start_feed_loop(self.camera_queue, loop)

            await asyncio.gather(start_screen(), start_camera())

    async def stop(self) -> None:
        """
        Cleanly and concurrently stops all active capture sources.
        """
        if not self._running:
            logger.warning("PerceptionBus is not running.")
            return

        self._running = False
        loop = asyncio.get_running_loop()

        logger.info("Stopping PerceptionBus capture sources...")

        # Concurrently call stop on active/all sources using asyncio.gather with run_in_executor
        # to ensure that blocking joins don't block the main event loop.
        stop_tasks = []

        if self.domain in ("digital", "hybrid"):
            stop_tasks.append(loop.run_in_executor(None, self.screen_capture.stop))

        if self.domain in ("physical", "hybrid"):
            stop_tasks.append(loop.run_in_executor(None, self.camera_feed.stop))

        if stop_tasks:
            await asyncio.gather(*stop_tasks)

        logger.info("PerceptionBus stopped successfully.")
