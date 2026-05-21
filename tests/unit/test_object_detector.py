import numpy as np
import pytest

from unittest.mock import MagicMock, patch

from core.models import Detection
from core.physical.object_detector import ObjectDetector


def test_missing_model_file():

    with pytest.raises(FileNotFoundError) as exc_info:

        ObjectDetector(
            "fake/path/yolo.pt",
            0.5
        )

    assert "download_models.py" in str(exc_info.value)


@patch("pathlib.Path.exists", return_value=True)
@patch("core.physical.object_detector.YOLO")
def test_detect_filters_low_confidence(
    mock_yolo,
    mock_exists
):
    mock_model = MagicMock()

    mock_yolo.return_value = mock_model

    # High confidence detection
    high_conf_box = MagicMock()
    high_conf_box.conf = [0.9]
    high_conf_box.cls = [0]
    high_conf_box.xyxy = [np.array([10, 20, 30, 40])]

    # Low confidence detection
    low_conf_box = MagicMock()
    low_conf_box.conf = [0.2]
    low_conf_box.cls = [1]
    low_conf_box.xyxy = [np.array([50, 60, 70, 80])]

    mock_result = MagicMock()

    mock_result.boxes = [
        high_conf_box,
        low_conf_box
    ]

    mock_result.names = {
        0: "person",
        1: "bicycle"
    }

    mock_model.return_value = [mock_result]

    detector = ObjectDetector(
        "fake_model.pt",
        0.5
    )

    frame = np.zeros((100, 100, 3))

    detections = detector.detect(frame)

    assert len(detections) == 1

    detection = detections[0]

    assert detection.label == "person"

    assert detection.confidence == pytest.approx(0.9)

    assert detection.bounding_box == [10, 20, 30, 40]


@patch("pathlib.Path.exists", return_value=True)
@patch("core.physical.object_detector.YOLO")
def test_draw_boxes_returns_annotated_frame(
    mock_yolo,
    mock_exists
):
    mock_model = MagicMock()

    mock_yolo.return_value = mock_model

    detector = ObjectDetector(
        "fake_model.pt",
        0.5
    )

    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    detections = [
        Detection(
            label="person",
            confidence=0.95,
            bounding_box=[10, 20, 30, 40]
        )
    ]

    annotated = detector.draw_boxes(
        frame,
        detections
    )

    assert isinstance(annotated, np.ndarray)

    assert annotated.shape == frame.shape