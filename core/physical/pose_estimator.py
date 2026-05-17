"""
Real-time pose estimation using MediaPipe Pose.

Estimates 33 body landmarks from a camera frame and classifies the
user's posture as ``"upright"``, ``"leaning"``, or ``"crouching"``
based on shoulder / hip / knee geometry.  Posture information is used
by the physical guidance pipeline to adjust tone — for example,
emitting a "lean back" warning when the user is too close to a hazard.
"""

from __future__ import annotations

import logging
import math
from typing import Optional

import numpy as np

from core.models import PoseResult

logger = logging.getLogger(__name__)

# MediaPipe is an optional heavy dependency.  Import lazily so the
# rest of the physical package stays importable when the library is
# absent (e.g. during lightweight CI runs or when the feature is
# disabled via ``POSE_ESTIMATION_ENABLED``).
try:
    import mediapipe as mp
except ImportError:  # pragma: no cover
    mp = None  # type: ignore[assignment]

# --- MediaPipe landmark indices (subset used for posture) --------
_LEFT_SHOULDER = 11
_RIGHT_SHOULDER = 12
_LEFT_HIP = 23
_RIGHT_HIP = 24
_LEFT_KNEE = 25
_RIGHT_KNEE = 26

# Landmark name mapping — covers all 33 MediaPipe Pose landmarks.
_LANDMARK_NAMES: dict[int, str] = {
    0: "NOSE",
    1: "LEFT_EYE_INNER",
    2: "LEFT_EYE",
    3: "LEFT_EYE_OUTER",
    4: "RIGHT_EYE_INNER",
    5: "RIGHT_EYE",
    6: "RIGHT_EYE_OUTER",
    7: "LEFT_EAR",
    8: "RIGHT_EAR",
    9: "MOUTH_LEFT",
    10: "MOUTH_RIGHT",
    11: "LEFT_SHOULDER",
    12: "RIGHT_SHOULDER",
    13: "LEFT_ELBOW",
    14: "RIGHT_ELBOW",
    15: "LEFT_WRIST",
    16: "RIGHT_WRIST",
    17: "LEFT_PINKY",
    18: "RIGHT_PINKY",
    19: "LEFT_INDEX",
    20: "RIGHT_INDEX",
    21: "LEFT_THUMB",
    22: "RIGHT_THUMB",
    23: "LEFT_HIP",
    24: "RIGHT_HIP",
    25: "LEFT_KNEE",
    26: "RIGHT_KNEE",
    27: "LEFT_ANKLE",
    28: "RIGHT_ANKLE",
    29: "LEFT_HEEL",
    30: "RIGHT_HEEL",
    31: "LEFT_FOOT_INDEX",
    32: "RIGHT_FOOT_INDEX",
}

# --- Posture classification thresholds --------------------------
# If the horizontal offset between the mid-shoulder and mid-hip
# exceeds this fraction of the frame, the user is "leaning".
_LEAN_THRESHOLD = 0.08

# If the angle at the knee (hip-knee-ankle proxy via hip-knee
# vertical) is below this value in degrees, classify as "crouching".
_CROUCH_KNEE_ANGLE_THRESHOLD = 120.0


class PoseEstimator:
    """Estimate body pose and classify posture from a camera frame.

    Uses *MediaPipe Pose* under the hood to detect 33 body landmarks.
    The caller should instantiate **once** and reuse across frames for
    best performance.

    Example::

        estimator = PoseEstimator()
        result = estimator.estimate(frame)
        if result:
            print(result.posture)
        estimator.close()
    """

    def __init__(
        self,
        *,
        static_image_mode: bool = False,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        """Initialise the MediaPipe Pose solution.

        Args:
            static_image_mode: Treat each frame independently when
                ``True``.  Set ``False`` for video streams.
            min_detection_confidence: Minimum confidence for person
                detection to be considered successful.
            min_tracking_confidence: Minimum confidence for landmark
                tracking between frames.

        Raises:
            RuntimeError: If the ``mediapipe`` package is not installed.
        """
        if mp is None:
            raise RuntimeError(
                "mediapipe is required for pose estimation. "
                "Install it with: pip install mediapipe"
            )

        self._pose = mp.solutions.pose.Pose(
            static_image_mode=static_image_mode,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        logger.info("PoseEstimator initialised")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def estimate(self, frame: np.ndarray) -> Optional[PoseResult]:
        """Process a single camera frame and return pose data.

        Args:
            frame: BGR image as a NumPy array (H × W × 3, ``uint8``).

        Returns:
            A :class:`PoseResult` with landmarks and classified posture,
            or ``None`` when no human pose is detected in the frame.
        """
        if frame is None or frame.size == 0:
            return None

        results = self._pose.process(frame)

        if not results.pose_landmarks:
            logger.debug("No pose detected in frame")
            return None

        landmarks = self._extract_landmarks(results.pose_landmarks)
        posture = self._classify_posture(results.pose_landmarks)

        return PoseResult(landmarks=landmarks, posture=posture)

    def get_guidance_adjustment(self, posture: str) -> Optional[str]:
        """Return a safety-oriented guidance string for *posture*.

        Args:
            posture: One of ``"leaning"``, ``"upright"``, or
                ``"crouching"``.

        Returns:
            A guidance adjustment message, or ``None`` when no
            adjustment is needed (i.e. the user is upright).
        """
        adjustments: dict[str, str] = {
            "leaning": (
                "⚠️  You appear to be leaning in — please lean back "
                "to maintain a safe distance from the work area."
            ),
            "crouching": (
                "🔽 You seem to be crouching — ensure you have a "
                "stable stance before handling tools or components."
            ),
        }
        return adjustments.get(posture)

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._pose.close()
        logger.info("PoseEstimator resources released")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _extract_landmarks(
        mp_landmarks: object,
    ) -> dict[str, tuple[float, float, float]]:
        """Convert MediaPipe landmarks to a named dictionary.

        Args:
            mp_landmarks: ``mediapipe.framework.formats
                .landmark_pb2.NormalizedLandmarkList``.

        Returns:
            Mapping from landmark name to ``(x, y, z)`` tuple with
            normalised coordinates.
        """
        named: dict[str, tuple[float, float, float]] = {}
        for idx, landmark in enumerate(mp_landmarks.landmark):
            name = _LANDMARK_NAMES.get(idx, f"LANDMARK_{idx}")
            named[name] = (landmark.x, landmark.y, landmark.z)
        return named

    @staticmethod
    def _classify_posture(mp_landmarks: object) -> str:
        """Classify posture from shoulder / hip / knee geometry.

        The algorithm uses two heuristics:

        1. **Lean detection** — if the horizontal midpoint of the
           shoulders differs significantly from that of the hips, the
           user is leaning forward or sideways.
        2. **Crouch detection** — if the angle formed at the knee
           (approximated from the hip → knee → vertical-below-knee
           vectors) is acute, the user is crouching.

        Falls back to ``"upright"`` when neither condition is met.

        Args:
            mp_landmarks: MediaPipe pose landmarks.

        Returns:
            ``"leaning"``, ``"crouching"``, or ``"upright"``.
        """
        lm = mp_landmarks.landmark

        # Mid-shoulder and mid-hip x-coordinates.
        mid_shoulder_x = (lm[_LEFT_SHOULDER].x + lm[_RIGHT_SHOULDER].x) / 2
        mid_hip_x = (lm[_LEFT_HIP].x + lm[_RIGHT_HIP].x) / 2

        if abs(mid_shoulder_x - mid_hip_x) > _LEAN_THRESHOLD:
            return "leaning"

        # Knee angle estimation (average of both legs).
        left_angle = _knee_angle(
            lm[_LEFT_HIP], lm[_LEFT_KNEE]
        )
        right_angle = _knee_angle(
            lm[_RIGHT_HIP], lm[_RIGHT_KNEE]
        )
        avg_knee_angle = (left_angle + right_angle) / 2

        if avg_knee_angle < _CROUCH_KNEE_ANGLE_THRESHOLD:
            return "crouching"

        return "upright"


# -------------------------------------------------------------------- #
# Module-level helpers
# -------------------------------------------------------------------- #


def _knee_angle(hip: object, knee: object) -> float:
    """Approximate the angle at *knee* in degrees.

    Uses the vectors hip→knee and a virtual vertical line below the
    knee.  A fully extended leg gives ~180°; a bent knee gives a
    smaller angle.

    Args:
        hip: Landmark with ``x``, ``y`` attributes.
        knee: Landmark with ``x``, ``y`` attributes.

    Returns:
        Angle in degrees (0–180).
    """
    # Vector from knee to hip.
    vec_kh = (hip.x - knee.x, hip.y - knee.y)
    # Virtual vertical vector pointing downward from knee.
    vec_down = (0.0, 1.0)

    dot = vec_kh[0] * vec_down[0] + vec_kh[1] * vec_down[1]
    mag_kh = math.hypot(*vec_kh)
    mag_down = 1.0

    if mag_kh == 0:
        return 180.0

    cos_angle = max(-1.0, min(1.0, dot / (mag_kh * mag_down)))
    return math.degrees(math.acos(cos_angle))
