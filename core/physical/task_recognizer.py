"""
Rule-based recognition of real-world tasks from visual detections and OCR text.
"""

from typing import Any, Protocol


class Detection(Protocol):
    """Minimal detection interface expected by TaskRecognizer."""

    label: str


class TaskRecognizer:
    """Recognize physical task categories from camera-frame signals."""

    COOKING_OBJECTS = {"knife", "bowl", "stove", "pot", "pan"}
    HARDWARE_REPAIR_OBJECTS = {"screwdriver", "wrench", "circuit_board", "wire"}
    FORM_KEYWORDS = ("name:", "date:", "signature", "___")

    TASK_GUIDANCE = {
        "cooking": [
            "Identify the ingredients and tools in front of you.",
            "Prepare a clean workspace before cutting or heating anything.",
            "Follow the recipe steps while keeping sharp and hot items controlled.",
            "Turn off appliances and clean the area when finished.",
        ],
        "hardware_repair": [
            "Disconnect power before handling hardware components.",
            "Inspect the device, wires, and fasteners for visible damage.",
            "Use the correct tool for each screw, connector, or board.",
            "Reassemble carefully and test the device in a safe state.",
        ],
        "form_filling": [
            "Read each field label before writing.",
            "Enter required personal details clearly.",
            "Check dates, signatures, and blank fields for completeness.",
            "Review the form once more before submitting it.",
        ],
        "document_reading": [
            "Scan the heading and structure of the document.",
            "Read the body text in sections.",
            "Note key facts, dates, and action items.",
            "Summarize the main point after reading.",
        ],
    }

    def recognize(self, detected_objects: list[Detection], ocr_text: str) -> str:
        """Return the most likely task type for the current frame."""
        object_labels = self._extract_labels(detected_objects)
        normalized_text = (ocr_text or "").lower()

        if object_labels & self.COOKING_OBJECTS:
            return "cooking"

        if object_labels & self.HARDWARE_REPAIR_OBJECTS:
            return "hardware_repair"

        if any(keyword in normalized_text for keyword in self.FORM_KEYWORDS):
            return "form_filling"

        known_tool_objects = self.COOKING_OBJECTS | self.HARDWARE_REPAIR_OBJECTS
        if len((ocr_text or "").split()) > 100 and not (object_labels & known_tool_objects):
            return "document_reading"

        return "unknown"

    def get_step_guidance(self, task_type: str) -> list[str]:
        """Return hardcoded guidance steps for a recognized task type."""
        return self.TASK_GUIDANCE.get(task_type, [])

    def _extract_labels(self, detected_objects: list[Detection]) -> set[str]:
        labels: set[str] = set()

        for detection in detected_objects or []:
            label = self._get_detection_label(detection)
            if label:
                labels.add(label.strip().lower())

        return labels

    def _get_detection_label(self, detection: Any) -> str:
        if isinstance(detection, str):
            return detection

        if isinstance(detection, dict):
            return str(
                detection.get("label")
                or detection.get("name")
                or detection.get("class_name")
                or detection.get("object")
                or ""
            )

        return str(
            getattr(detection, "label", None)
            or getattr(detection, "name", None)
            or getattr(detection, "class_name", None)
            or getattr(detection, "object", None)
            or ""
        )
