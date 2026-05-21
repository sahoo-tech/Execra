import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.perception.camera_feed import CameraFeed
from core.perception.screen_capture import ScreenCapture
from core.perception.perception_bus import PerceptionBus


def test_perception_bus_initialization():
    """Test that PerceptionBus initializes correctly and validates domains."""
    bus = PerceptionBus(domain="digital")
    assert bus.domain == "digital"
    assert isinstance(bus.screen_capture, ScreenCapture)
    assert isinstance(bus.camera_feed, CameraFeed)
    assert isinstance(bus.screen_queue, asyncio.Queue)
    assert isinstance(bus.camera_queue, asyncio.Queue)

    # Test invalid domains
    with pytest.raises(ValueError):
        PerceptionBus(domain="invalid_domain")


@pytest.mark.asyncio
async def test_perception_bus_calls_screen_only_in_digital_domain():
    """Verify that in digital domain, only screen capture is started and stopped."""
    mock_screen = MagicMock(spec=ScreenCapture)
    mock_camera = MagicMock(spec=CameraFeed)

    bus = PerceptionBus(
        domain="digital", screen_capture=mock_screen, camera_feed=mock_camera
    )

    await bus.start()
    mock_screen.start_capture_loop.assert_called_once_with(bus.screen_queue)
    mock_camera.start_feed_loop.assert_not_called()

    await bus.stop()
    mock_screen.stop.assert_called_once()
    mock_camera.stop.assert_not_called()


@pytest.mark.asyncio
async def test_perception_bus_calls_camera_only_in_physical_domain():
    """Verify that in physical domain, only camera capture is started and stopped."""
    mock_screen = MagicMock(spec=ScreenCapture)
    mock_camera = MagicMock(spec=CameraFeed)

    bus = PerceptionBus(
        domain="physical", screen_capture=mock_screen, camera_feed=mock_camera
    )

    await bus.start()
    mock_screen.start_capture_loop.assert_not_called()
    mock_camera.start_feed_loop.assert_called_once()

    # Retrieve the loop passed to camera start loop
    args, kwargs = mock_camera.start_feed_loop.call_args
    assert args[0] == bus.camera_queue
    assert isinstance(args[1], asyncio.AbstractEventLoop)

    await bus.stop()
    mock_screen.stop.assert_not_called()
    mock_camera.stop.assert_called_once()


@pytest.mark.asyncio
async def test_perception_bus_calls_both_in_hybrid_domain():
    """Verify that in hybrid domain, both captures are started concurrently and stopped."""
    mock_screen = MagicMock(spec=ScreenCapture)
    mock_camera = MagicMock(spec=CameraFeed)

    bus = PerceptionBus(
        domain="hybrid", screen_capture=mock_screen, camera_feed=mock_camera
    )

    await bus.start()
    mock_screen.start_capture_loop.assert_called_once_with(bus.screen_queue)
    mock_camera.start_feed_loop.assert_called_once()

    await bus.stop()
    mock_screen.stop.assert_called_once()
    mock_camera.stop.assert_called_once()


@pytest.mark.asyncio
@patch("core.perception.screen_capture.mss.mss")
@patch("cv2.VideoCapture")
async def test_perception_bus_integration_flow(mock_video_capture, mock_mss):
    """
    Deep integration test running actual capturing threads (with mocked hardware)
    to verify queue routing in hybrid mode.
    """
    # Mock screen capture MSS backend
    mock_sct = MagicMock()
    mock_sct.monitors = [None, {}]
    fake_screen_frame = np.zeros((10, 10, 4), dtype=np.uint8)
    fake_screen_frame[0, 0] = [10, 20, 30, 255]  # BGRA
    mock_sct.grab.return_value = fake_screen_frame
    mock_mss.return_value.__enter__.return_value = mock_sct

    # Mock camera capture CV2 backend
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    fake_camera_frame = np.ones((10, 10, 3), dtype=np.uint8) * 128
    mock_cap.read.return_value = (True, fake_camera_frame)
    mock_video_capture.return_value = mock_cap

    # Instantiate real modules with mocked hardware
    screen_cap = ScreenCapture(fps=10)
    camera_feed = CameraFeed(fps=10)

    bus = PerceptionBus(
        domain="hybrid", screen_capture=screen_cap, camera_feed=camera_feed
    )

    # Start the bus
    await bus.start()

    try:
        # Give capture threads a brief moment to run and enqueue frames
        await asyncio.sleep(0.3)

        # Check screen queue has frames
        assert not bus.screen_queue.empty()
        screen_frame = await bus.screen_queue.get()
        assert isinstance(screen_frame, np.ndarray)
        assert screen_frame.shape == (10, 10, 3)
        # Verify BGRA -> RGB conversion in ScreenCapture
        assert screen_frame[0, 0].tolist() == [30, 20, 10]

        # Check camera queue has frames
        assert not bus.camera_queue.empty()
        camera_frame = await bus.camera_queue.get()
        assert isinstance(camera_frame, np.ndarray)
        assert camera_frame.shape == (10, 10, 3)
        assert camera_frame[0, 0].tolist() == [128, 128, 128]

    finally:
        # Cleanly stop both captures
        await bus.stop()

    # Verify that the capture threads are stopped
    assert not screen_cap.thread.is_alive()
    assert not camera_feed.thread.is_alive()
