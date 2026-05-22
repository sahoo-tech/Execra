"""
Unit tests for core/perception/camera_feed.py
"""

import asyncio
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
def test_stop_releases_camera(mock_video_capture):
    """Test stop releases camera resource."""

    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    camera_feed.stop()

    mock_cap.release.assert_called_once()
    assert camera_feed.running is False


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

@patch("core.perception.camera_feed.time.sleep")
@patch("cv2.VideoCapture")
def test_retry_behavior_when_camera_unavailable(
    mock_video_capture,
    mock_sleep,
):
    """Test retry logic when camera is unavailable."""

    mock_cap = MagicMock()

    mock_cap.isOpened.return_value = False

    mock_video_capture.return_value = mock_cap

    camera_feed = CameraFeed()

    queue = asyncio.Queue()

    loop = asyncio.new_event_loop()

    camera_feed.running = True

    def stop_after_retry(*args, **kwargs):
        camera_feed.running = False

    mock_sleep.side_effect = stop_after_retry

    camera_feed._feed_loop(queue, loop)

    assert mock_video_capture.called
    assert mock_sleep.called
