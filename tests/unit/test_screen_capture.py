import asyncio
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
def test_start_capture_loop(mock_mss):
    """
    Test starting the capture loop thread and queuing frames.
    """

    async def run_test():

        mock_sct = MagicMock()

        mock_sct.monitors = [None, {}]

        fake_frame = np.zeros(
            (1, 1, 4),
            dtype=np.uint8,
        )

        fake_frame[0, 0] = [10, 20, 30, 255]

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=10)

        queue = asyncio.Queue(maxsize=2)

        capture.start_capture_loop(queue)

        try:
            await asyncio.sleep(0.3)

            assert capture.thread is not None
            assert capture.thread.is_alive()

            assert not queue.empty()

            frame = await queue.get()

            assert isinstance(frame, np.ndarray)

            assert frame.shape == (1, 1, 3)

            # Verify BGRA to RGB
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

        fake_frame = np.zeros(
            (50, 50, 4),
            dtype=np.uint8,
        )

        mock_sct.grab.return_value = fake_frame

        mock_mss.return_value.__enter__.return_value = mock_sct

        capture = ScreenCapture(fps=10)

        queue = asyncio.Queue(maxsize=2)

        capture.start_capture_loop(queue)

        try:
            await asyncio.sleep(0.1)

        finally:
            capture.stop()

        assert capture._stop_event.is_set()

        assert capture.thread is not None
        assert not capture.thread.is_alive()

    asyncio.run(run_test())
