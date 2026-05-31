import asyncio
import logging
import threading
import time

import cv2
import numpy as np


class CameraFeed:
    """Capture webcam frames and push them into an asyncio queue."""

    def __init__(self, camera_index: int = 0, fps: int = 5):
        """
        Initialize the camera feed.

        Args:
            camera_index: Webcam device index.
            fps: Frames captured per second.
        """

        self.camera_index = camera_index
        self.fps = fps
        self.cap = cv2.VideoCapture(self.camera_index)

        if self.cap is None or not self.cap.isOpened():
            logging.warning("Failed to open camera")

        self.running = False
        self.delay = 1 / self.fps
        self.thread: threading.Thread | None = None

    def read_frame(self) -> np.ndarray | None:
        """
        Read a single frame from the webcam.

        Returns:
            np.ndarray | None:
                Captured frame if successful, otherwise None.
        """

        if self.cap is None or not self.cap.isOpened():
            logging.warning("Camera is unavailable")
            return None

        success, frame = self.cap.read()

        if not success or frame is None:
            logging.warning("Failed to read frame")
            return None

        return frame

    def start_feed_loop(
        self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop
    ) -> None:
        """
        Start the threaded camera feed loop.

        Args:
            queue: Asyncio queue used to store frames.
            loop: Running asyncio event loop.
        """

        if self.thread is not None and self.thread.is_alive():
            return

        self.thread = threading.Thread(
            target=self._feed_loop, args=(queue, loop), daemon=True
        )

        self.thread.start()

    def _feed_loop(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        """
        Continuously capture frames and push them into the queue.
        """

        self.running = True

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                logging.warning(
                    "Camera unavailable. Retrying connection in 5 seconds..."
                )

                time.sleep(5)

                if self.cap is not None:
                    self.cap.release()

                self.cap = cv2.VideoCapture(self.camera_index)
                continue

            frame = self.read_frame()

            if frame is not None:
                asyncio.run_coroutine_threadsafe(queue.put(frame), loop)

            time.sleep(self.delay)

    def stop(self) -> None:
        """Stop the camera feed and release resources."""

        self.running = False

        if self.thread is not None:
            self.thread.join()

        if self.cap is not None:
            self.cap.release()
