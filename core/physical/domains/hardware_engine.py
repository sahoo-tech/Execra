# core/physical/domains/hardware_engine.py
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class GuidanceInstruction:
    status: str
    message: str
    critical_warning: bool
    detected_components: List[str]

class HardwareEngine:
    def __init__(self):
        # Component dictionary matching
        self.component_dictionary = {
            "screwdriver": "Tool: Screwdriver",
            "m3_screw": "Fastener: M3 Screw",
            "heat_sink": "Component: Heat Sink",
            "circuit_board": "Component: Circuit Board",
            "esd_strap": "Safety: ESD Strap",
            "soldering_iron": "Tool: Soldering Iron",
            "power_tool": "Tool: Power Tool",
            "safety_glasses": "Safety: Safety Glasses"
        }
        
        # Built-in step templates
        self.templates = [
            "PC assembly", 
            "circuit board repair", 
            "appliance disassembly", 
            "cable management"
        ]

    def analyze(self, detections: List[Dict[str, Any]], hand_results: Any, ocr_text: str) -> GuidanceInstruction:
        """
        Analyzes the current frame detections and enforces hardware repair safety rules.
        """
        # Extract detected class names (Assuming detection dict has a 'class' key)
        # e.g., detections = [{"class": "circuit_board", "bbox": [...]}, ...]
        detected_classes = [det.get("class", "").lower() for det in detections]
        
        critical_warning = False
        message = "Step validation passed. Safe to proceed."
        status = "OK"
        
        # Rule 1: Circuit board detected without ESD strap in frame
        if "circuit_board" in detected_classes and "esd_strap" not in detected_classes:
            critical_warning = True
            status = "CRITICAL_WARNING"
            message = "CRITICAL: Circuit board detected. Please wear an ESD strap to prevent static damage."
            
        # Rule 3: Power tool detected without safety glasses in frame
        elif "power_tool" in detected_classes and "safety_glasses" not in detected_classes:
            critical_warning = True
            status = "CRITICAL_WARNING"
            message = "CRITICAL: Power tool detected. Safety glasses are required before proceeding."

        # Rule 2: Soldering iron proximity warning
        elif "soldering_iron" in detected_classes:
            status = "WARNING"
            message = "WARNING: Soldering iron active. Ensure it is kept away from non-target components and wires."
            # Note: For strict proximity, you would calculate distance between bounding boxes here.

        # Match detected objects against the component dictionary
        matched_components = [
            self.component_dictionary.get(cls, f"Unknown: {cls}") 
            for cls in detected_classes
        ]

        return GuidanceInstruction(
            status=status,
            message=message,
            critical_warning=critical_warning,
            detected_components=list(set(matched_components)) # Remove duplicates
        )