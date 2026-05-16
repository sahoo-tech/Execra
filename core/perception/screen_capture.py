import asyncio
import logging
import threading
import time
from typing import Optional

import mss
import numpy as np

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Continuously captures screen frames at a configured FPS.
    """

    def __init__(self, fps: int = 10) -> None:
        """
        Initialize the screen capture system.

        Args:
            fps (int): Frames per second for capture.

        Raises:
            ValueError: If fps <= 0
        """
        if fps <= 0:
            raise ValueError("FPS must be greater than 0")

        self.fps = fps
        self.frame_interval = 1.0 / fps

        # Thread-safe stop signal
        self._stop_event = threading.Event()

        self.thread: Optional[threading.Thread] = None

    def _run_loop(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        """
        Internal capture loop running in a separate thread.

        Args:
            queue (asyncio.Queue): Queue to place frames into.
            loop (asyncio.AbstractEventLoop): Main asyncio event loop.
        """

        try:
            # Create MSS inside the worker thread
            with mss.mss() as sct:

                monitor = sct.monitors[1]

                while not self._stop_event.is_set():

                    start_time = time.time()

                    try:
                        screenshot = sct.grab(monitor)

                        # Convert screenshot to RGB numpy array
                        frame = np.asarray(screenshot)[:, :, :3]
                        frame = frame[:, :, ::-1]

                        def safe_put() -> None:
                            try:
                                queue.put_nowait(frame)
                                logger.debug("Frame queued successfully")

                            except asyncio.QueueFull:
                                logger.warning("Frame dropped: queue full")

                        # Schedule queue insertion safely
                        loop.call_soon_threadsafe(safe_put)

                    except Exception as e:
                        logger.error("Capture loop error: %s", e)

                    elapsed = time.time() - start_time

                    sleep_time = max(0, self.frame_interval - elapsed)

                    time.sleep(sleep_time)

        except Exception as e:
            logger.error("Failed to initialize screen capture: %s", e)

    def start_capture_loop(self, queue: asyncio.Queue) -> None:
        """
        Start continuous screen capture in a separate thread.

        Args:
            queue (asyncio.Queue): Queue to place frames into.
        """

        if self.thread and self.thread.is_alive():
            logger.debug("Capture loop already running")
            return

        try:
            current_loop = asyncio.get_running_loop()

        except RuntimeError as e:
            logger.error("No running asyncio event loop: %s", e)
            raise

        self._stop_event.clear()

        self.thread = threading.Thread(
            target=self._run_loop,
            args=(queue, current_loop),
            daemon=True,
        )

        self.thread.start()

        logger.debug("Screen capture thread started")

    def stop(self) -> None:
        """
        Stop the capture loop cleanly.
        """

        self._stop_event.set()

        if self.thread and self.thread.is_alive():

            self.thread.join(timeout=2)

            if self.thread.is_alive():
                logger.warning("Capture thread did not stop cleanly")

        logger.debug("Screen capture stopped")
