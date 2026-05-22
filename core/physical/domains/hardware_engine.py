"""
core/physical/domains/hardware_engine.py
=========================================
Hardware Repair Domain Guidance Engine.

Analyses a single perception frame (object detections, hand landmarks, OCR)
and returns a structured GuidanceInstruction with safety-critical warnings
and step guidance appropriate to the current hardware repair task.

Safety priority (highest to lowest):
  1. CRITICAL_WARNING — must be resolved before any work continues
  2. WARNING          — proceed with care
  3. OK               — all safety checks passed

Multiple hazards in a single frame are ALL reported (comma-separated message),
so no warning is silently dropped by elif short-circuit logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class GuidanceInstruction:
    status: str                          # "OK" | "WARNING" | "CRITICAL_WARNING"
    message: str                         # Human-readable, actionable guidance
    critical_warning: bool               # True if any CRITICAL rule triggered
    detected_components: List[str]       # Mapped component names (no duplicates)
    active_template: Optional[str] = None  # Which step template is in use


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bbox_center(bbox: List[float]) -> Tuple[float, float]:
    """Return (cx, cy) for a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    return (x1 + x2) / 2.0, (y1 + y2) / 2.0


def _bbox_distance(bbox_a: List[float], bbox_b: List[float]) -> float:
    """Euclidean distance between the centres of two bounding boxes."""
    cx_a, cy_a = _bbox_center(bbox_a)
    cx_b, cy_b = _bbox_center(bbox_b)
    return math.hypot(cx_a - cx_b, cy_a - cy_b)


# ---------------------------------------------------------------------------
# HardwareEngine
# ---------------------------------------------------------------------------

class HardwareEngine:
    """
    Guidance engine for hardware repair tasks.

    Step templates
    --------------
    The engine picks the most relevant built-in step template from
    ``self.templates`` by matching detected component classes against
    known template keywords. The chosen template is surfaced in the
    returned ``GuidanceInstruction.active_template`` field so that the
    caller (e.g. IntelligenceCore) can display contextual step instructions.

    Safety rules
    ------------
    Rules are evaluated INDEPENDENTLY (not elif) so that every hazard
    present in a frame is reported in the same message.

      Rule 1: circuit_board without esd_strap          → CRITICAL_WARNING
      Rule 2: soldering_iron within proximity_threshold
               pixels of any non-target component       → WARNING
      Rule 3: power_tool without safety_glasses         → CRITICAL_WARNING
    """

    # Proximity threshold in pixels. Soldering iron within this distance of
    # a non-target component triggers a warning.
    SOLDERING_PROXIMITY_THRESHOLD: float = 150.0

    # Component dictionary: detection class → human-readable label
    component_dictionary: Dict[str, str] = {
        "screwdriver":    "Tool: Screwdriver",
        "m3_screw":       "Fastener: M3 Screw",
        "heat_sink":      "Component: Heat Sink",
        "circuit_board":  "Component: Circuit Board",
        "esd_strap":      "Safety: ESD Strap",
        "soldering_iron": "Tool: Soldering Iron",
        "power_tool":     "Tool: Power Tool",
        "safety_glasses": "Safety: Safety Glasses",
    }

    # Step templates: name → list of component keywords that indicate this task
    templates: Dict[str, List[str]] = {
        "PC assembly":            ["circuit_board", "heat_sink", "screwdriver", "m3_screw"],
        "circuit board repair":   ["circuit_board", "soldering_iron", "esd_strap"],
        "appliance disassembly":  ["screwdriver", "power_tool", "safety_glasses"],
        "cable management":       ["screwdriver"],
    }

    def __init__(self) -> None:
        # Re-expose as instance attributes so callers can introspect/override
        self.component_dictionary = dict(HardwareEngine.component_dictionary)
        self.templates = dict(HardwareEngine.templates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        detections: List[Dict[str, Any]],
        hand_results: Any,
        ocr_text: str,
    ) -> GuidanceInstruction:
        """
        Analyse the current perception frame and return a GuidanceInstruction.

        Parameters
        ----------
        detections:
            List of detected objects. Each dict must have a ``"class"`` key
            (str) and may optionally have a ``"bbox"`` key ([x1, y1, x2, y2])
            for proximity calculations.
        hand_results:
            MediaPipe / hand-landmark output. Reserved for future gesture-based
            rules (e.g. "hand approaching soldering iron tip").
        ocr_text:
            Raw OCR text extracted from the frame. Used to surface part numbers
            or repair step labels mentioned in the scene.
        """
        # Normalise: extract class names as lowercase strings
        detected_classes: List[str] = [
            det.get("class", "").lower() for det in detections
        ]

        # ------------------------------------------------------------------
        # Collect all triggered messages INDEPENDENTLY (no elif)
        # ------------------------------------------------------------------
        critical_messages: List[str] = []
        warning_messages: List[str] = []

        # Rule 1: circuit board without ESD strap → CRITICAL
        if (
            "circuit_board" in detected_classes
            and "esd_strap" not in detected_classes
        ):
            critical_messages.append(
                "Circuit board detected without an ESD strap — "
                "wear an ESD strap immediately to prevent static damage."
            )

        # Rule 3: power tool without safety glasses → CRITICAL
        if (
            "power_tool" in detected_classes
            and "safety_glasses" not in detected_classes
        ):
            critical_messages.append(
                "Power tool detected without safety glasses — "
                "put on safety glasses before proceeding."
            )

        # Rule 2: soldering iron proximity to non-target components → WARNING
        if "soldering_iron" in detected_classes:
            proximity_breach = self._check_soldering_proximity(detections)
            if proximity_breach:
                warning_messages.append(
                    f"Soldering iron is within {self.SOLDERING_PROXIMITY_THRESHOLD:.0f}px "
                    f"of '{proximity_breach}' — move iron away from non-target components."
                )
            else:
                warning_messages.append(
                    "Soldering iron active — keep it away from non-target components and wires."
                )

        # ------------------------------------------------------------------
        # OCR integration: surface part numbers / step labels
        # ------------------------------------------------------------------
        if ocr_text.strip():
            ocr_note = self._parse_ocr(ocr_text)
            if ocr_note:
                warning_messages.append(ocr_note)

        # ------------------------------------------------------------------
        # Build unified status and message
        # ------------------------------------------------------------------
        if critical_messages:
            status = "CRITICAL_WARNING"
            critical_warning = True
            all_parts = ["CRITICAL: " + m for m in critical_messages]
            if warning_messages:
                all_parts += ["WARNING: " + m for m in warning_messages]
            message = " | ".join(all_parts)
        elif warning_messages:
            status = "WARNING"
            critical_warning = False
            message = " | ".join("WARNING: " + m for m in warning_messages)
        else:
            status = "OK"
            critical_warning = False
            message = "Step validation passed. Safe to proceed."

        # ------------------------------------------------------------------
        # Component identification
        # ------------------------------------------------------------------
        matched_components = list({
            self.component_dictionary.get(cls, f"Unknown: {cls}")
            for cls in detected_classes
            if cls  # skip empty strings from missing "class" keys
        })

        # ------------------------------------------------------------------
        # Step template selection
        # ------------------------------------------------------------------
        active_template = self._select_template(detected_classes)

        return GuidanceInstruction(
            status=status,
            message=message,
            critical_warning=critical_warning,
            detected_components=matched_components,
            active_template=active_template,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_soldering_proximity(
        self, detections: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Return the class name of the closest non-target component to the
        soldering iron if it is within SOLDERING_PROXIMITY_THRESHOLD pixels,
        or None if no proximity breach.

        Falls back gracefully when bounding boxes are absent (returns None).
        """
        iron_det = next(
            (d for d in detections if d.get("class", "").lower() == "soldering_iron"),
            None,
        )
        if iron_det is None or "bbox" not in iron_det:
            return None  # no bbox data available; skip proximity check

        iron_bbox = iron_det["bbox"]

        # Components considered "non-target" — not the iron itself and not
        # intentional soldering targets like the circuit board during repair.
        non_target_classes = {
            "esd_strap", "screwdriver", "m3_screw",
            "heat_sink", "power_tool", "safety_glasses",
        }

        closest_name: Optional[str] = None
        closest_dist = float("inf")

        for det in detections:
            cls = det.get("class", "").lower()
            if cls not in non_target_classes:
                continue
            if "bbox" not in det:
                continue
            dist = _bbox_distance(iron_bbox, det["bbox"])
            if dist < closest_dist:
                closest_dist = dist
                closest_name = cls

        if closest_dist < self.SOLDERING_PROXIMITY_THRESHOLD:
            return closest_name
        return None

    def _select_template(self, detected_classes: List[str]) -> Optional[str]:
        """
        Return the template name with the most keyword matches against
        the detected classes. Returns None if no class matches any template.
        """
        best_template: Optional[str] = None
        best_score = 0

        for template_name, keywords in self.templates.items():
            score = sum(1 for kw in keywords if kw in detected_classes)
            if score > best_score:
                best_score = score
                best_template = template_name

        return best_template if best_score > 0 else None

    def _parse_ocr(self, ocr_text: str) -> Optional[str]:
        """
        Extract actionable information from OCR text.

        Currently surfaces part numbers (strings matching typical P/N formats)
        and step headings. Extend this for richer repair-manual parsing.
        """
        import re

        # Look for step headings like "Step 3:" or "STEP 3 –"
        step_match = re.search(r"step\s*(\d+)", ocr_text, re.IGNORECASE)
        if step_match:
            return f"OCR detected repair step {step_match.group(1)} in frame."

        # Look for part numbers like PN-1234 or P/N: AB-5678
        pn_match = re.search(r"p/?n[:\s-]*([A-Z0-9\-]+)", ocr_text, re.IGNORECASE)
        if pn_match:
            return f"OCR detected part number: {pn_match.group(1)}."

        return None