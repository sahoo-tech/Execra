"""
tests/test_hardware_engine.py
==============================
Unit tests for HardwareEngine — every safety rule, edge case,
template selection, OCR integration, and proximity detection.

Run with:
    pytest tests/test_hardware_engine.py -v
"""

import pytest
from core.physical.domains.hardware_engine import HardwareEngine


@pytest.fixture
def engine():
    return HardwareEngine()


# ---------------------------------------------------------------------------
# Rule 1: circuit_board without ESD strap
# ---------------------------------------------------------------------------

class TestCircuitBoardRule:

    def test_circuit_board_missing_esd_strap(self, engine):
        """Original test — must still pass."""
        detections = [{"class": "circuit_board"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is True
        assert result.status == "CRITICAL_WARNING"
        assert "ESD strap" in result.message

    def test_circuit_board_with_esd_strap_ok(self, engine):
        """When ESD strap is present, no critical warning for this rule."""
        detections = [{"class": "circuit_board"}, {"class": "esd_strap"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is False
        assert "ESD" not in result.message or result.status != "CRITICAL_WARNING"


# ---------------------------------------------------------------------------
# Rule 3: power_tool without safety_glasses
# ---------------------------------------------------------------------------

class TestPowerToolRule:

    def test_power_tool_missing_safety_glasses(self, engine):
        """Original test — must still pass."""
        detections = [{"class": "power_tool"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is True
        assert result.status == "CRITICAL_WARNING"
        assert "safety glasses" in result.message.lower()

    def test_power_tool_with_safety_glasses_ok(self, engine):
        detections = [{"class": "power_tool"}, {"class": "safety_glasses"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is False


# ---------------------------------------------------------------------------
# Rule 2: soldering iron
# ---------------------------------------------------------------------------

class TestSolderingIronRule:

    def test_soldering_iron_warning_no_bbox(self, engine):
        """Original test — must still pass (no bbox data → generic warning)."""
        detections = [{"class": "soldering_iron"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is False
        assert result.status == "WARNING"
        assert "Soldering iron" in result.message

    def test_soldering_iron_proximity_breach(self, engine):
        """Soldering iron bbox within threshold of a non-target component."""
        detections = [
            {"class": "soldering_iron", "bbox": [100, 100, 150, 150]},
            {"class": "m3_screw",       "bbox": [160, 100, 200, 140]},  # ~10px away
        ]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.status == "WARNING"
        assert "m3_screw" in result.message or "proximity" in result.message.lower()

    def test_soldering_iron_no_proximity_breach(self, engine):
        """Soldering iron far from all non-target components → generic warning only."""
        detections = [
            {"class": "soldering_iron", "bbox": [0, 0, 50, 50]},
            {"class": "m3_screw",       "bbox": [1000, 1000, 1100, 1100]},
        ]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.status == "WARNING"
        assert "m3_screw" not in result.message


# ---------------------------------------------------------------------------
# Safe operations (original test)
# ---------------------------------------------------------------------------

class TestSafeOperations:

    def test_all_safety_gear_present(self, engine):
        """Original test — must still pass."""
        detections = [
            {"class": "power_tool"},
            {"class": "safety_glasses"},
            {"class": "circuit_board"},
            {"class": "esd_strap"},
        ]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is False
        assert result.status == "OK"


# ---------------------------------------------------------------------------
# FIX VERIFICATION: multiple simultaneous hazards (was broken by elif)
# ---------------------------------------------------------------------------

class TestMultipleSimultaneousHazards:

    def test_both_critical_rules_fire_simultaneously(self, engine):
        """
        power_tool (no glasses) + circuit_board (no ESD) in the same frame.
        BOTH critical warnings must appear — the old elif code silently dropped
        one of them.
        """
        detections = [
            {"class": "power_tool"},
            {"class": "circuit_board"},
        ]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is True
        assert result.status == "CRITICAL_WARNING"
        assert "ESD" in result.message or "static" in result.message.lower()
        assert "safety glasses" in result.message.lower() or "glasses" in result.message.lower()

    def test_critical_and_soldering_warning_together(self, engine):
        """
        circuit_board (no ESD) + soldering iron → CRITICAL takes priority
        but soldering warning is still surfaced in the same message.
        """
        detections = [
            {"class": "circuit_board"},
            {"class": "soldering_iron"},
        ]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.critical_warning is True
        assert "Soldering iron" in result.message or "soldering" in result.message.lower()


# ---------------------------------------------------------------------------
# Template selection
# ---------------------------------------------------------------------------

class TestTemplateSelection:

    def test_pc_assembly_template_selected(self, engine):
        detections = [{"class": "circuit_board"}, {"class": "esd_strap"},
                      {"class": "screwdriver"}, {"class": "heat_sink"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.active_template == "PC assembly"

    def test_circuit_board_repair_template(self, engine):
        detections = [{"class": "soldering_iron"}, {"class": "esd_strap"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.active_template == "circuit board repair"

    def test_no_template_when_no_match(self, engine):
        detections = [{"class": "unknown_widget"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.active_template is None

    def test_appliance_disassembly_template(self, engine):
        detections = [{"class": "power_tool"}, {"class": "safety_glasses"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.active_template == "appliance disassembly"


# ---------------------------------------------------------------------------
# OCR integration
# ---------------------------------------------------------------------------

class TestOCRIntegration:

    def test_ocr_step_number_surfaced(self, engine):
        result = engine.analyze([], hand_results=None, ocr_text="Step 3: Remove heat sink")
        assert "step 3" in result.message.lower() or "step" in result.message.lower()

    def test_ocr_part_number_surfaced(self, engine):
        result = engine.analyze([], hand_results=None, ocr_text="P/N: AB-5678")
        assert "AB-5678" in result.message

    def test_empty_ocr_no_extra_message(self, engine):
        result = engine.analyze([], hand_results=None, ocr_text="")
        assert result.status == "OK"
        assert result.message == "Step validation passed. Safe to proceed."


# ---------------------------------------------------------------------------
# Component identification
# ---------------------------------------------------------------------------

class TestComponentIdentification:

    def test_known_components_mapped_correctly(self, engine):
        detections = [{"class": "screwdriver"}, {"class": "m3_screw"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert "Tool: Screwdriver" in result.detected_components
        assert "Fastener: M3 Screw" in result.detected_components

    def test_unknown_component_reported(self, engine):
        detections = [{"class": "unknown_widget"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert any("Unknown" in c for c in result.detected_components)

    def test_no_duplicate_components(self, engine):
        detections = [{"class": "screwdriver"}, {"class": "screwdriver"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.detected_components.count("Tool: Screwdriver") == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_empty_detections(self, engine):
        result = engine.analyze([], hand_results=None, ocr_text="")
        assert result.status == "OK"
        assert result.critical_warning is False
        assert result.detected_components == []

    def test_uppercase_class_normalised(self, engine):
        """CV models may return mixed-case class names — should still trigger rules."""
        detections = [{"class": "Circuit_Board"}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.status == "CRITICAL_WARNING"

    def test_missing_class_key_does_not_crash(self, engine):
        """Detections missing the 'class' key should be handled gracefully."""
        detections = [{"bbox": [0, 0, 100, 100]}]
        result = engine.analyze(detections, hand_results=None, ocr_text="")
        assert result.status == "OK"

    def test_hand_results_none_does_not_crash(self, engine):
        result = engine.analyze([], hand_results=None, ocr_text="")
        assert result is not None