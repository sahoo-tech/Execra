"""
Unit tests for core/perception/camera_feed.py
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import numpy as np

from core.perception.camera_feed import CameraFeed


@patch("cv2.VideoCapture")
def test_camera_feed_initialization(mock_video_capture):
    """Test CameraFeed initializes correctly."""

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    assert camera_feed.camera_index == 0
    assert camera_feed.fps == 5
    assert camera_feed.cap == mock_cap
    assert camera_feed.running is False
    assert camera_feed.thread is None


@patch("cv2.VideoCapture")
def test_read_frame_success(mock_video_capture):
    """Test successful frame reading."""

    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, fake_frame)

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    frame = camera_feed.read_frame()

    assert frame is not None
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)
    assert np.array_equal(frame, fake_frame)


@patch("cv2.VideoCapture")
def test_read_frame_failure(mock_video_capture):
    """Test failed frame read returns None."""

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    frame = camera_feed.read_frame()

    assert frame is None


@patch("cv2.VideoCapture")
def test_camera_unavailable(mock_video_capture):
    """Test unavailable camera returns None."""

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    frame = camera_feed.read_frame()

    assert frame is None


@patch.object(CameraFeed, "_feed_loop")
@patch("cv2.VideoCapture")
def test_thread_starts(mock_video_capture, mock_feed_loop):
    """Test feed loop thread starts correctly."""

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    queue = asyncio.Queue()
    loop = asyncio.new_event_loop()

    camera_feed.start_feed_loop(queue, loop)

    assert camera_feed.thread is not None

    mock_feed_loop.assert_called_once()

    camera_feed.stop()

    loop.close()


@patch("core.perception.camera_feed.time.sleep", return_value=None)
@patch("cv2.VideoCapture")
def test_camera_retry_behavior(mock_video_capture, mock_sleep):
    """Test retry logic when camera is initially unavailable."""
    failed_cap = MagicMock()
    failed_cap.isOpened.return_value = False

    working_cap = MagicMock()
    working_cap.isOpened.return_value = True
    working_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))

    mock_video_capture.side_effect = [failed_cap, working_cap]

    camera_feed = CameraFeed()
    queue = asyncio.Queue()
    loop = asyncio.new_event_loop()

    # Prevent the loop from actually running indefinitely or queuing coroutines
    def mock_read_frame_stop():
        camera_feed.running = False
        return None  # Returning None safely skips the asyncio coroutine scheduling block entirely

    camera_feed.read_frame = mock_read_frame_stop
    camera_feed._feed_loop(queue, loop)

    assert mock_video_capture.call_count >= 2
    assert mock_sleep.called
    assert camera_feed.cap == working_cap

    loop.close()


@patch("core.perception.camera_feed.cv2.VideoCapture")
def test_feed_loop_puts_frames_in_queue(mock_video_capture):
    """
    Test feed loop pushes frames into asyncio queue.
    """

    async def run_test():

        fake_frame = np.zeros((240, 320, 3), dtype=np.uint8)

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, fake_frame)

        mock_video_capture.return_value = mock_cap

        camera_feed = CameraFeed(fps=10)

        queue = asyncio.Queue(maxsize=10)

        loop = asyncio.get_running_loop()

        start_time = time.time()

        camera_feed.start_feed_loop(queue, loop)

        try:
            await asyncio.sleep(0.5)

            elapsed = time.time() - start_time

            assert not queue.empty()

            frame_count = queue.qsize()

            expected_frames = camera_feed.fps * elapsed

            assert frame_count >= max(1, expected_frames * 0.4)

            frame = await queue.get()

            assert isinstance(frame, np.ndarray)

            assert frame.shape == (240, 320, 3)

        finally:
            camera_feed.stop()

        assert camera_feed.thread is not None
        assert not camera_feed.thread.is_alive()

    asyncio.run(run_test())


@patch("core.perception.camera_feed.asyncio.run_coroutine_threadsafe")
@patch("cv2.VideoCapture")
def test_stop_releases_camera(mock_video_capture, mock_run_coroutine):
    """Test stop releases camera resource."""
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, fake_frame)

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()
    queue = asyncio.Queue()
    loop = asyncio.new_event_loop()

    camera_feed.start_feed_loop(queue, loop)
    time.sleep(0.1)

    start_time = time.time()
    camera_feed.stop()
    elapsed = time.time() - start_time

    assert elapsed < 1
    mock_cap.release.assert_called()
    assert camera_feed.running is False
    assert camera_feed.thread is not None
    assert not camera_feed.thread.is_alive()

    loop.close()


@patch("core.perception.camera_feed.asyncio.run_coroutine_threadsafe")
@patch("cv2.VideoCapture")
def test_start_feed_loop_when_already_running(mock_video_capture, mock_run_coroutine):
    """Test start_feed_loop does not create another thread if running."""
    fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, fake_frame)

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()
    queue = asyncio.Queue()
    loop = asyncio.new_event_loop()

    camera_feed.start_feed_loop(queue, loop)
    time.sleep(0.1)
    first_thread = camera_feed.thread

    # Attempt to start again
    camera_feed.start_feed_loop(queue, loop)
    time.sleep(0.1)

    assert camera_feed.thread is first_thread
    camera_feed.stop()
    loop.close()
