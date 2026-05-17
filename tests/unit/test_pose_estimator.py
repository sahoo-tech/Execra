"""
Unit tests for ``core.physical.pose_estimator``.

All tests mock the MediaPipe Pose output to avoid requiring a camera
or GPU during CI.  The structure mirrors the project's existing test
patterns (see ``tests/unit/test_task_recognizer.py``).
"""

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.models import PoseResult
from core.physical.pose_estimator import (
    PoseEstimator,
    _LANDMARK_NAMES,
    _knee_angle,
)


# ------------------------------------------------------------------ #
# Helpers — lightweight stand-ins for MediaPipe protobuf objects
# ------------------------------------------------------------------ #


@dataclass
class FakeLandmark:
    """Mimics ``mediapipe.framework.formats.landmark_pb2
    .NormalizedLandmark``."""

    x: float
    y: float
    z: float


def _make_landmarks(overrides: dict[int, tuple[float, float, float]]):
    """Build a fake landmark list with sensible defaults.

    By default every landmark is placed at ``(0.5, 0.5, 0.0)``; pass
    *overrides* to set specific indices.
    """
    landmarks = [FakeLandmark(0.5, 0.5, 0.0) for _ in range(33)]
    for idx, (x, y, z) in overrides.items():
        landmarks[idx] = FakeLandmark(x, y, z)
    return SimpleNamespace(landmark=landmarks)


def _make_pose_results(landmarks_obj, detected: bool = True):
    """Wrap landmarks into a result object that mimics MP Pose."""
    return SimpleNamespace(
        pose_landmarks=landmarks_obj if detected else None,
    )


# ------------------------------------------------------------------ #
# Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture
def _patch_mediapipe():
    """Patch ``mediapipe.solutions.pose.Pose`` for the estimator."""
    mock_pose_instance = MagicMock()
    # Default: return upright landmarks.
    upright = _make_landmarks({
        11: (0.45, 0.3, 0.0),   # LEFT_SHOULDER
        12: (0.55, 0.3, 0.0),   # RIGHT_SHOULDER
        23: (0.45, 0.6, 0.0),   # LEFT_HIP
        24: (0.55, 0.6, 0.0),   # RIGHT_HIP
        25: (0.45, 0.85, 0.0),  # LEFT_KNEE
        26: (0.55, 0.85, 0.0),  # RIGHT_KNEE
    })
    mock_pose_instance.process.return_value = _make_pose_results(
        upright
    )

    with patch(
        "core.physical.pose_estimator.mp"
    ) as mock_mp:
        mock_mp.solutions.pose.Pose.return_value = mock_pose_instance
        yield mock_mp, mock_pose_instance


# ------------------------------------------------------------------ #
# Test: estimate() — valid detection
# ------------------------------------------------------------------ #


class TestEstimateWithValidFrame:
    """PoseEstimator.estimate returns a PoseResult on success."""

    def test_returns_pose_result(self, _patch_mediapipe):
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert isinstance(result, PoseResult)

    def test_result_has_landmarks_and_posture(self, _patch_mediapipe):
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is not None
        assert isinstance(result.landmarks, dict)
        assert result.posture in {"leaning", "upright", "crouching"}

    def test_landmark_keys_are_named(self, _patch_mediapipe):
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is not None
        assert "LEFT_SHOULDER" in result.landmarks
        assert "RIGHT_HIP" in result.landmarks


# ------------------------------------------------------------------ #
# Test: estimate() — no detection
# ------------------------------------------------------------------ #


class TestEstimateNoDetection:
    """PoseEstimator.estimate returns None when no pose is found."""

    def test_returns_none_on_empty_frame(self, _patch_mediapipe):
        estimator = PoseEstimator()

        result = estimator.estimate(np.array([]))

        assert result is None

    def test_returns_none_on_none_frame(self, _patch_mediapipe):
        estimator = PoseEstimator()

        result = estimator.estimate(None)

        assert result is None

    def test_returns_none_when_mediapipe_detects_nothing(
        self, _patch_mediapipe
    ):
        _, mock_pose = _patch_mediapipe
        mock_pose.process.return_value = _make_pose_results(
            None, detected=False
        )
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is None


# ------------------------------------------------------------------ #
# Test: posture classification
# ------------------------------------------------------------------ #


class TestClassifyPosture:
    """Posture is classified from shoulder / hip / knee geometry."""

    def test_upright_posture(self, _patch_mediapipe):
        """Shoulder and hip aligned ≈ vertically → upright."""
        _, mock_pose = _patch_mediapipe
        upright = _make_landmarks({
            11: (0.48, 0.3, 0.0),
            12: (0.52, 0.3, 0.0),
            23: (0.48, 0.6, 0.0),
            24: (0.52, 0.6, 0.0),
            25: (0.48, 0.85, 0.0),
            26: (0.52, 0.85, 0.0),
        })
        mock_pose.process.return_value = _make_pose_results(upright)
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is not None
        assert result.posture == "upright"

    def test_leaning_posture(self, _patch_mediapipe):
        """Large horizontal offset between shoulder/hip → leaning."""
        _, mock_pose = _patch_mediapipe
        leaning = _make_landmarks({
            11: (0.30, 0.3, 0.0),
            12: (0.40, 0.3, 0.0),
            23: (0.50, 0.6, 0.0),
            24: (0.60, 0.6, 0.0),
            25: (0.50, 0.85, 0.0),
            26: (0.60, 0.85, 0.0),
        })
        mock_pose.process.return_value = _make_pose_results(leaning)
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is not None
        assert result.posture == "leaning"

    def test_crouching_posture(self, _patch_mediapipe):
        """Acute knee angle → crouching."""
        _, mock_pose = _patch_mediapipe
        crouching = _make_landmarks({
            11: (0.49, 0.3, 0.0),
            12: (0.51, 0.3, 0.0),
            23: (0.49, 0.6, 0.0),
            24: (0.51, 0.6, 0.0),
            # Knees raised high → sharp angle.
            25: (0.49, 0.55, 0.0),
            26: (0.51, 0.55, 0.0),
        })
        mock_pose.process.return_value = _make_pose_results(crouching)
        estimator = PoseEstimator()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        result = estimator.estimate(frame)

        assert result is not None
        assert result.posture == "crouching"


# ------------------------------------------------------------------ #
# Test: guidance adjustment
# ------------------------------------------------------------------ #


class TestGuidanceAdjustment:
    """get_guidance_adjustment returns context-aware text."""

    def test_leaning_returns_warning(self, _patch_mediapipe):
        estimator = PoseEstimator()

        text = estimator.get_guidance_adjustment("leaning")

        assert text is not None
        assert "lean back" in text.lower()

    def test_crouching_returns_warning(self, _patch_mediapipe):
        estimator = PoseEstimator()

        text = estimator.get_guidance_adjustment("crouching")

        assert text is not None
        assert "crouching" in text.lower()

    def test_upright_returns_none(self, _patch_mediapipe):
        estimator = PoseEstimator()

        assert estimator.get_guidance_adjustment("upright") is None


# ------------------------------------------------------------------ #
# Test: resource cleanup
# ------------------------------------------------------------------ #


class TestClose:
    """close() releases MediaPipe resources."""

    def test_close_calls_pose_close(self, _patch_mediapipe):
        _, mock_pose = _patch_mediapipe
        estimator = PoseEstimator()

        estimator.close()

        mock_pose.close.assert_called_once()


# ------------------------------------------------------------------ #
# Test: _knee_angle helper
# ------------------------------------------------------------------ #


class TestKneeAngle:
    """Module-level _knee_angle helper returns sensible angles."""

    def test_straight_leg_approximately_180(self):
        hip = FakeLandmark(0.5, 0.4, 0.0)
        knee = FakeLandmark(0.5, 0.7, 0.0)

        angle = _knee_angle(hip, knee)

        # Straight leg: hip directly above knee → vector points up,
        # down vector points down → angle ≈ 180.
        assert 170.0 <= angle <= 180.0

    def test_bent_knee_less_than_180(self):
        hip = FakeLandmark(0.3, 0.4, 0.0)
        knee = FakeLandmark(0.5, 0.7, 0.0)

        angle = _knee_angle(hip, knee)

        assert angle < 170.0

    def test_zero_length_vector_returns_180(self):
        hip = FakeLandmark(0.5, 0.5, 0.0)
        knee = FakeLandmark(0.5, 0.5, 0.0)

        angle = _knee_angle(hip, knee)

        assert angle == 180.0


# ------------------------------------------------------------------ #
# Test: landmark name mapping completeness
# ------------------------------------------------------------------ #


class TestLandmarkNames:
    """_LANDMARK_NAMES covers all 33 MediaPipe Pose landmarks."""

    def test_has_33_entries(self):
        assert len(_LANDMARK_NAMES) == 33

    def test_indices_are_0_to_32(self):
        assert set(_LANDMARK_NAMES.keys()) == set(range(33))
