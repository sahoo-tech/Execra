import asyncio
import logging
import struct
import threading
import time
from multiprocessing import Event as MPEvent
from multiprocessing import Process, shared_memory
from typing import Optional

import cv2
import mss
import numpy as np

logger = logging.getLogger(__name__)

HEADER_FORMAT = "!II"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_SHARED_MEMORY_SIZE = 5 * 1024 * 1024
SHMEM_NAME = "execra_capture_frame"


class AdaptiveFPSController:
    def __init__(self, window_size: int = 10, default_fps: int = 2) -> None:
        self.window_size = window_size
        self.default_fps = default_fps
        self._deltas: list[float] = []

    def update(self, delta_pct: float) -> int:
        self._deltas.append(delta_pct)
        if len(self._deltas) > self.window_size:
            self._deltas.pop(0)
        if not self._deltas:
            return self.default_fps
        avg_delta = sum(self._deltas) / len(self._deltas)
        if avg_delta < 1.0:
            return 1
        if avg_delta <= 10.0:
            return self.default_fps
        return 5

    def reset(self) -> None:
        self._deltas.clear()


def compute_delta_pct(prev: Optional[np.ndarray], curr: np.ndarray) -> float:
    if prev is None or prev.shape != curr.shape:
        return 0.0
    diff = np.mean(np.abs(curr.astype(np.float32) - prev.astype(np.float32)))
    return (diff / 255.0) * 100.0


def _capture_process(
    shm_name: str,
    shm_size: int,
    default_fps: int,
    jpeg_quality: int,
    stop_event: MPEvent,
) -> None:
    shm = shared_memory.SharedMemory(name=shm_name)
    try:
        controller = AdaptiveFPSController(default_fps=default_fps)
        prev_frame: Optional[np.ndarray] = None
        counter = 0

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            while not stop_event.is_set():
                start_time = time.time()
                try:
                    screenshot = sct.grab(monitor)
                    frame_bgr = np.asarray(screenshot)[:, :, :3]

                    delta_pct = compute_delta_pct(prev_frame, frame_bgr)
                    prev_frame = frame_bgr.copy()
                    current_fps = controller.update(delta_pct)

                    _, buffer = cv2.imencode(
                        ".jpg", frame_bgr,
                        [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality],
                    )
                    jpeg_bytes = buffer.tobytes()
                    data_size = len(jpeg_bytes)

                    if data_size + HEADER_SIZE > shm_size:
                        logger.warning("Frame too large for shared memory")
                        continue

                    counter += 1
                    header = struct.pack(HEADER_FORMAT, counter, data_size)
                    shm.buf[:HEADER_SIZE] = header
                    shm.buf[HEADER_SIZE:HEADER_SIZE + data_size] = jpeg_bytes
                except Exception as e:
                    logger.error("Capture loop error: %s", e)

                elapsed = time.time() - start_time
                sleep_time = max(0, (1.0 / current_fps) - elapsed)
                for _ in range(int(sleep_time / 0.05) + 1):
                    if stop_event.is_set():
                        break
                    time.sleep(0.05)
    finally:
        shm.close()


class ScreenCapture:
    def __init__(
        self,
        fps: int = 2,
        max_shared_memory_size: int = MAX_SHARED_MEMORY_SIZE,
        jpeg_quality: int = 85,
    ) -> None:
        if fps <= 0:
            raise ValueError("FPS must be greater than 0")
        self.fps = fps
        self.max_shared_memory_size = max_shared_memory_size
        self.jpeg_quality = jpeg_quality
        self._stop_event = threading.Event()
        self._stop_mp_event = MPEvent()
        self._process: Optional[Process] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._shm: Optional[shared_memory.SharedMemory] = None

    def start_capture_loop(self, queue: asyncio.Queue) -> None:
        if self._process and self._process.is_alive():
            logger.debug("Capture process already running")
            return
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError as e:
            logger.error("No running asyncio event loop: %s", e)
            raise

        try:
            existing = shared_memory.SharedMemory(name=SHMEM_NAME)
            existing.close()
            existing.unlink()
        except FileNotFoundError:
            pass

        self._shm = shared_memory.SharedMemory(
            name=SHMEM_NAME, create=True, size=self.max_shared_memory_size,
        )
        self._shm.buf[:HEADER_SIZE] = b'\x00' * HEADER_SIZE

        self._stop_event.clear()
        self._stop_mp_event.clear()

        self._process = Process(
            target=_capture_process,
            args=(
                SHMEM_NAME,
                self.max_shared_memory_size,
                self.fps,
                self.jpeg_quality,
                self._stop_mp_event,
            ),
            daemon=True,
        )
        self._process.start()

        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            args=(queue, current_loop),
            daemon=True,
        )
        self._reader_thread.start()
        logger.debug("Screen capture process started (PID %s)", self._process.pid)

    def _reader_loop(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop) -> None:
        shm = shared_memory.SharedMemory(name=SHMEM_NAME)
        prev_counter = 0
        try:
            while not self._stop_event.is_set():
                try:
                    header = bytes(shm.buf[:HEADER_SIZE])
                    counter, data_size = struct.unpack(HEADER_FORMAT, header)

                    if counter != prev_counter and data_size > 0:
                        prev_counter = counter
                        jpeg_bytes = bytes(shm.buf[HEADER_SIZE:HEADER_SIZE + data_size])
                        np_arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
                        frame_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                        if frame_bgr is not None:
                            frame = frame_bgr[:, :, ::-1]

                            def safe_put(f=frame):
                                try:
                                    queue.put_nowait(f)
                                except asyncio.QueueFull:
                                    logger.warning("Frame dropped: queue full")

                            loop.call_soon_threadsafe(safe_put)
                except Exception:
                    pass
                time.sleep(0.05)
        finally:
            shm.close()

    def stop(self) -> None:
        self._stop_event.set()
        self._stop_mp_event.set()
        if self._process and self._process.is_alive():
            self._process.join(timeout=3)
            if self._process.is_alive():
                logger.warning("Capture process did not stop cleanly")
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)
            if self._reader_thread.is_alive():
                logger.warning("Reader thread did not stop cleanly")
        if self._shm:
            self._shm.close()
            self._shm.unlink()
        logger.debug("Screen capture stopped")
