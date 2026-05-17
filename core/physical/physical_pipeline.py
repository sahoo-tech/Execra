"""
Orchestrator for the physical-domain processing pipeline.

Composes :class:`TaskRecognizer` and (optionally)
:class:`PoseEstimator` into a single processing step that takes a
camera frame plus detected objects and returns an enriched result with
task type, guidance steps, and posture-based adjustments.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from core.config import settings
from core.models import PoseResult
from core.physical.task_recognizer import TaskRecognizer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Aggregated output of a single physical-pipeline run.

    Attributes:
        task_type: Recognised physical task, e.g. ``"cooking"``.
        guidance_steps: Ordered guidance strings for the task.
        pose: Pose estimation result, if available.
        posture_guidance: Safety adjustment text driven by posture.
    """

    task_type: str
    guidance_steps: list[str] = field(default_factory=list)
    pose: Optional[PoseResult] = None
    posture_guidance: Optional[str] = None


class PhysicalPipeline:
    """End-to-end physical domain processing pipeline.

    The pipeline always runs task recognition.  Pose estimation is
    added **only** when the ``POSE_ESTIMATION_ENABLED`` configuration
    flag is ``True`` and the ``mediapipe`` library is available.

    Example::

        pipeline = PhysicalPipeline()
        result = pipeline.run(frame, detections, ocr_text)
        print(result.task_type, result.posture_guidance)
        pipeline.close()
    """

    def __init__(self) -> None:
        self._recognizer = TaskRecognizer()
        self._pose_estimator: Any = None

        if settings.POSE_ESTIMATION_ENABLED:
            try:
                from core.physical.pose_estimator import PoseEstimator

                self._pose_estimator = PoseEstimator()
                logger.info(
                    "PhysicalPipeline: pose estimation enabled"
                )
            except (ImportError, RuntimeError) as exc:
                logger.warning(
                    "Pose estimation requested but unavailable: %s",
                    exc,
                )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def run(
        self,
        frame: np.ndarray,
        detected_objects: list[Any],
        ocr_text: str = "",
    ) -> PipelineResult:
        """Execute the full physical-domain pipeline.

        Args:
            frame: Camera frame (BGR, uint8).
            detected_objects: List of detection objects / dicts with a
                ``label`` attribute or key.
            ocr_text: Raw OCR text extracted from the frame.

        Returns:
            A :class:`PipelineResult` with all available data.
        """
        task_type = self._recognizer.recognize(
            detected_objects, ocr_text
        )
        guidance_steps = self._recognizer.get_step_guidance(task_type)

        pose: Optional[PoseResult] = None
        posture_guidance: Optional[str] = None

        if self._pose_estimator is not None:
            pose = self._pose_estimator.estimate(frame)
            if pose is not None:
                posture_guidance = (
                    self._pose_estimator.get_guidance_adjustment(
                        pose.posture
                    )
                )

        return PipelineResult(
            task_type=task_type,
            guidance_steps=guidance_steps,
            pose=pose,
            posture_guidance=posture_guidance,
        )

    def close(self) -> None:
        """Release all pipeline resources."""
        if self._pose_estimator is not None:
            self._pose_estimator.close()
        logger.info("PhysicalPipeline resources released")
