from pathlib import Path
import numpy as np
import cv2
from ultralytics import YOLO
import time

from core.config import settings
from core.models import Detection
from core.logger import get_logger

logger = get_logger(__name__)

class ObjectDetector:
    """YOLOv8-based object detector."""

    def __init__(self, model_path: str, threshold: float):
        model_file = Path(model_path)

        if not model_file.exists():
            raise FileNotFoundError(
                f"YOLO model file not found at {model_path}. "
                "Run scripts/download_models.py first."
            )

        self.threshold = threshold or settings.DETECTION_THRESHOLD
        self.model = YOLO(str(model_file))
    
    def detect(self, frame: np.ndarray) -> list[Detection]:
        """
        Run YOLO inference on a frame and return filtered detections.
        """
        start_time = time.perf_counter()
        results = self.model(frame)
        elapsed = time.perf_counter() - start_time

        logger.debug(
            "YOLO inference completed in %.4f seconds",
            elapsed
        )
        
        detections: list[Detection] = []

        for result in results:
            for box in result.boxes:
                confidence = float(box.conf[0])

                if confidence < self.threshold:
                    continue

                class_id = int(box.cls[0])
                label = result.names[class_id]

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0].tolist()
                )

                detections.append(
                    Detection(
                        label=label,
                        confidence=confidence,
                        bounding_box=[x1, y1, x2, y2]
                    )
                )
        
        return detections

    def draw_boxes(self, frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        """
        Draw bounding boxes and labels on a frame.
        """
        annotated_frame = frame.copy()

        for detection in detections:
            x1, y1, x2, y2 = detection.bounding_box

            label = (
                f"{detection.label} "
                f"{detection.confidence:.2f}"
            )

            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            cv2.putText(annotated_frame, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return annotated_frame