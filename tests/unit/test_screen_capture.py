import asyncio
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.perception.screen_capture import ScreenCapture


def test_screen_capture_initialization():
    """
    Test ScreenCapture initialization.
    """

    capture = ScreenCapture(fps=30)

    assert capture.fps == 30
    assert capture.thread is None
    assert not capture._stop_event.is_set()


def test_invalid_fps():
    """
    Test invalid FPS values.
    """

    with pytest.raises(ValueError):
        ScreenCapture(fps=0)

    with pytest.raises(ValueError):
        ScreenCapture(fps=-5)


@patch("core.perception.screen_capture.mss.mss")
def test_capture_frame(mock_mss):
    """
    Test capture_frame returns a valid RGB numpy array.
    """

    mock_sct = MagicMock()

    mock_sct.monitors = [None, {}]

    fake_frame = np.zeros((50, 50, 4), dtype=np.uint8)

    # BGRA
    fake_frame[:, :] = [10, 20, 30, 255]

    mock_sct.grab.return_value = fake_frame

    mock_mss.return_value.__enter__.return_value = mock_sct

    capture = ScreenCapture(fps=10)

    frame = capture.capture_frame()

    assert isinstance(frame, np.ndarray)

    assert frame.shape == (50, 50, 3)

    # Verify BGRA to RGB conversion
    assert frame[0, 0].tolist() == [30, 20, 10]


@patch("core.perception.screen_capture.mss.mss")
def test_start_capture_loop(mock_mss):
    """
    Test starting the capture loop thread and queuing frames.
    """

    async def run_test():

        mock_sct = MagicMock()

        mock_sct.monitors = [None, {}]

        fake_frame = np.zeros((10, 10, 4), dtype=np.uint8)

        fake_frame[:, :] = [10, 20, 30, 255]

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=10)

        queue = asyncio.Queue(maxsize=20)

        start_time = time.time()

        capture.start_capture_loop(queue)

        try:
            await asyncio.sleep(0.5)

            elapsed = time.time() - start_time

            assert capture.thread is not None
            assert capture.thread.is_alive()

            assert not queue.empty()

            frame_count = queue.qsize()

            # FPS validation
            expected_frames = capture.fps * elapsed

            assert frame_count >= max(1, expected_frames * 0.4)

            frame = await queue.get()

            assert isinstance(frame, np.ndarray)

            assert frame.shape == (10, 10, 3)

            # Verify RGB conversion
            assert frame[0, 0].tolist() == [30, 20, 10]

        finally:
            capture.stop()

        assert not capture.thread.is_alive()

    asyncio.run(run_test())


@patch("core.perception.screen_capture.mss.mss")
def test_stop_capture(mock_mss):
    """
    Test stopping the capture loop cleanly.
    """

    async def run_test():

        mock_sct = MagicMock()

        mock_sct.monitors = [None, {}]

        fake_frame = np.zeros((50, 50, 4), dtype=np.uint8)

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=10)

        queue = asyncio.Queue(maxsize=2)

        capture.start_capture_loop(queue)

        await asyncio.sleep(0.2)

        start_time = time.time()

        capture.stop()

        elapsed = time.time() - start_time

        assert elapsed < 1
        assert capture._stop_event.is_set()
        assert capture.thread is not None
        assert not capture.thread.is_alive()

    asyncio.run(run_test())


@patch("core.perception.screen_capture.mss.mss")
def test_start_capture_loop_when_already_running(mock_mss):
    """
    Test start_capture_loop does not create a new thread
    if one is already running.
    """

    async def run_test():

        mock_sct = MagicMock()

        mock_sct.monitors = [None, {}]

        fake_frame = np.zeros((10, 10, 4), dtype=np.uint8)

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=10)

        queue = asyncio.Queue(maxsize=5)

        capture.start_capture_loop(queue)

        await asyncio.sleep(0.1)

        first_thread = capture.thread

        # Attempt to start again
        capture.start_capture_loop(queue)

        await asyncio.sleep(0.1)

        assert capture.thread is first_thread

        capture.stop()

    asyncio.run(run_test())


@patch("core.perception.screen_capture.mss.mss")
def test_queue_full_branch(mock_mss):
    """
    Test frames are dropped safely when queue is full.
    """

    async def run_test():

        mock_sct = MagicMock()

        mock_sct.monitors = [None, {}]

        fake_frame = np.zeros((10, 10, 4), dtype=np.uint8)

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=30)

        # Small queue to force QueueFull branch
        queue = asyncio.Queue(maxsize=1)

        # Fill queue immediately
        await queue.put(np.zeros((10, 10, 3)))

        capture.start_capture_loop(queue)

        await asyncio.sleep(0.2)

        assert queue.full()

        capture.stop()

    asyncio.run(run_test())


def test_start_capture_loop_without_running_loop():
    """
    Test start_capture_loop raises RuntimeError
    when no asyncio loop is running.
    """

    capture = ScreenCapture(fps=10)

    queue = asyncio.Queue()

    with pytest.raises(RuntimeError):
        capture.start_capture_loop(queue)
