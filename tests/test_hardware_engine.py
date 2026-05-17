# tests/test_hardware_engine.py
import pytest
from core.physical.domains.hardware_engine import HardwareEngine

@pytest.fixture
def engine():
    return HardwareEngine()

def test_circuit_board_missing_esd_strap(engine):
    # Setup: Only circuit board is detected
    detections = [{"class": "circuit_board"}]
    result = engine.analyze(detections, hand_results=None, ocr_text="")
    
    # Assert
    assert result.critical_warning is True
    assert result.status == "CRITICAL_WARNING"
    assert "ESD strap" in result.message

def test_power_tool_missing_safety_glasses(engine):
    # Setup: Power tool detected, no glasses
    detections = [{"class": "power_tool"}]
    result = engine.analyze(detections, hand_results=None, ocr_text="")
    
    # Assert
    assert result.critical_warning is True
    assert "Safety glasses" in result.message

def test_soldering_iron_warning(engine):
    # Setup: Soldering iron detected
    detections = [{"class": "soldering_iron"}]
    result = engine.analyze(detections, hand_results=None, ocr_text="")
    
    # Assert
    assert result.critical_warning is False
    assert result.status == "WARNING"
    assert "Soldering iron active" in result.message

def test_safe_operations(engine):
    # Setup: Tools present with correct safety gear
    detections = [
        {"class": "power_tool"}, 
        {"class": "safety_glasses"},
        {"class": "circuit_board"},
        {"class": "esd_strap"}
    ]
    result = engine.analyze(detections, hand_results=None, ocr_text="")
    
    # Assert
    assert result.critical_warning is False
    assert result.status == "OK"