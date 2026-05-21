import asyncio
from unittest.mock import MagicMock, PropertyMock, patch

import numpy as np
import pytest

from core.perception.screen_capture import (
    SHMEM_NAME,
    AdaptiveFPSController,
    ScreenCapture,
    compute_delta_pct,
)


def test_initialization():
    capture = ScreenCapture(fps=2)
    assert capture.fps == 2
    assert capture._process is None
    assert capture._reader_thread is None
    assert not capture._stop_event.is_set()
    assert not capture._stop_mp_event.is_set()


def test_invalid_fps():
    with pytest.raises(ValueError):
        ScreenCapture(fps=0)
    with pytest.raises(ValueError):
        ScreenCapture(fps=-5)


def test_adaptive_fps_controller_low_delta():
    controller = AdaptiveFPSController(window_size=3, default_fps=2)
    for _ in range(5):
        controller.update(0.5)
    assert controller.update(0.5) == 1


def test_adaptive_fps_controller_medium_delta():
    controller = AdaptiveFPSController(window_size=3, default_fps=2)
    for _ in range(5):
        controller.update(5.0)
    assert controller.update(5.0) == 2


def test_adaptive_fps_controller_high_delta():
    controller = AdaptiveFPSController(window_size=3, default_fps=2)
    for _ in range(5):
        controller.update(50.0)
    assert controller.update(50.0) == 5


def test_adaptive_fps_controller_mixed():
    controller = AdaptiveFPSController(window_size=3, default_fps=4)
    controller.update(0.5)
    controller.update(0.5)
    controller.update(0.5)
    assert controller.update(0.5) == 1
    controller.reset()
    controller.update(15.0)
    controller.update(15.0)
    controller.update(15.0)
    assert controller.update(15.0) == 5


def test_adaptive_fps_controller_empty():
    controller = AdaptiveFPSController(default_fps=3)
    assert controller.update(0.0) == 1


def test_compute_delta_pct_no_prev():
    curr = np.zeros((10, 10, 3), dtype=np.uint8)
    assert compute_delta_pct(None, curr) == 0.0


def test_compute_delta_pct_identical():
    frame = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    assert compute_delta_pct(frame, frame.copy()) == 0.0


def test_compute_delta_pct_max_diff():
    prev = np.zeros((10, 10, 3), dtype=np.uint8)
    curr = np.full((10, 10, 3), 255, dtype=np.uint8)
    assert compute_delta_pct(prev, curr) == 100.0


def test_compute_delta_pct_shape_mismatch():
    prev = np.zeros((10, 10, 3), dtype=np.uint8)
    curr = np.zeros((20, 20, 3), dtype=np.uint8)
    assert compute_delta_pct(prev, curr) == 0.0


@patch("core.perception.screen_capture.shared_memory.SharedMemory")
@patch("core.perception.screen_capture.Process")
async def test_start_capture_loop(mock_process, mock_shm):
    mock_shm_instance = MagicMock()
    mock_buf = bytearray(1024 * 1024)
    type(mock_shm_instance).buf = PropertyMock(return_value=mock_buf)
    mock_shm.return_value = mock_shm_instance

    mock_process_instance = MagicMock()
    mock_process.return_value = mock_process_instance

    capture = ScreenCapture(fps=2)
    queue = asyncio.Queue(maxsize=2)

    capture.start_capture_loop(queue)

    mock_process.assert_called_once()
    _, kwargs = mock_process.call_args
    assert kwargs["target"].__name__ == "_capture_process"
    assert kwargs["args"][0] == SHMEM_NAME
    assert kwargs["args"][2] == 2
    assert kwargs["daemon"] is True
    mock_process_instance.start.assert_called_once()

    assert capture._reader_thread is not None
    assert capture._reader_thread.is_alive()
    assert capture._process is not None

    capture.stop()


@patch("core.perception.screen_capture.shared_memory.SharedMemory")
@patch("core.perception.screen_capture.Process")
async def test_stop_capture(mock_process, mock_shm):
    mock_shm_instance = MagicMock()
    mock_buf = bytearray(1024 * 1024)
    type(mock_shm_instance).buf = PropertyMock(return_value=mock_buf)
    mock_shm.return_value = mock_shm_instance

    mock_process_instance = MagicMock()
    mock_process_instance.is_alive.return_value = True
    mock_process.return_value = mock_process_instance

    capture = ScreenCapture(fps=2)
    queue = asyncio.Queue(maxsize=2)
    capture.start_capture_loop(queue)

    mock_process_instance.reset_mock()
    mock_shm_instance.reset_mock()

    capture.stop()

    assert capture._stop_event.is_set()
    assert capture._stop_mp_event.is_set()
    mock_process_instance.join.assert_called_once_with(timeout=3)
    assert mock_shm_instance.close.called
    assert mock_shm_instance.unlink.called
