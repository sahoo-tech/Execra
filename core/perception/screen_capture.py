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

    def __init__(self, fps: int = 10, delta_threshold: float = 2.0) -> None:
        """
        Initialize the screen capture system.

        Args:
            fps (int): Frames per second for capture.
            delta_threshold (float): Threshold for pixel changes to queue a frame.

        Raises:
            ValueError: If fps <= 0
        """
        if fps <= 0:
            raise ValueError("FPS must be greater than 0")

        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.delta_detector = DeltaDetector(delta_threshold)

        # Metrics
        self.frames_captured = 0
        self.frames_forwarded = 0
        self.frames_dropped = 0

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
                prev_frame = None

                while not self._stop_event.is_set():

                    start_time = time.time()

                    try:
                        screenshot = sct.grab(monitor)
                        self.frames_captured += 1

                        # Convert screenshot to RGB numpy array
                        frame = np.asarray(screenshot)[:, :, :3]
                        frame = frame[:, :, ::-1]

                        
                        if prev_frame is None or self.delta_detector.has_changed(prev_frame, frame):
                            prev_frame = frame

                            def safe_put(f=frame) -> None:
                                try:
                                    queue.put_nowait(f)
                                    self.frames_forwarded += 1
                                    logger.debug("Frame queued successfully")

                                except asyncio.QueueFull:
                                    self.frames_dropped += 1
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

    def get_stats(self) -> dict:
        """
        Returns the current frame capture metrics.
        """
        return {
            "frames_captured": self.frames_captured,
            "frames_forwarded": self.frames_forwarded,
            "frames_dropped": self.frames_dropped
        }

class DeltaDetector:
    """
    Detects changes between two video frames based on a specified threshold.
    """
    
    def __init__(self, threshold: float) -> None:
        """
        Initialize the DeltaDetector.

        Args:
            threshold (float): The mean absolute pixel difference threshold 
                               above which a frame is considered changed.
        """
        self.threshold = threshold

    def has_changed(self, prevFrame: np.ndarray, currFrame: np.ndarray) -> bool:
        """
        Calculates the mean absolute pixel difference between two frames.
        Returns True if the difference exceeds the given threshold.

        Args:
            prevFrame (np.ndarray): The old frame.
            currFrame (np.ndarray): The current frame.

        Returns:
            bool: True if the mean difference is strictly greater than the threshold.
        """

        # Checking frame dimensions
        if prevFrame.shape != currFrame.shape:
            return True

        diff = np.abs(prevFrame.astype(np.int16) - currFrame.astype(np.int16))
        
        mean_diff = float(np.mean(diff))
        
        return mean_diff > self.threshold

    def get_changes(self, prevFrame: np.ndarray, currFrame: np.ndarray) -> float:
        """
        Calculates the percentage of the frame that has changed.

        Args:
            prevFrame (np.ndarray): The old frame.
            currFrame (np.ndarray): The current frame.

        Returns:
            float: The percentage of pixels that differ between the frames (0.0 to 100.0).
        """

        if prevFrame.shape != currFrame.shape:
            return 100.0

        changed_pixels = np.any(prevFrame != currFrame, axis=-1)
        
        return float(np.mean(changed_pixels)) * 100.0