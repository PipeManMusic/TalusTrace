import pytest
from core.logic import check_bend_radius_violations

def test_ph4_3_2_bend_radius_violation():
    """
    Validates that sharp turns are flagged based on wire diameter.
    Rule: Min Bend Radius = 4x Diameter.
    """
    wire_diameter = 2.0  # mm
    # A 90-degree turn with only 2mm of travel is too sharp for an 8mm radius requirement
    sharp_path = [(0,0), (2,0), (2,2)]
    
    violation = check_bend_radius_violations(sharp_path, wire_diameter)
    
    assert violation is not None
    assert "BEND_RADIUS" in violation["category"]
    assert violation["severity"] == "ERROR"

def test_ph4_3_2_compliant_bend():
    """Validates that a smooth path passes the audit."""
    wire_diameter = 2.0
    smooth_path = [(0,0), (20,0), (20,20)] # 20mm turn is > 8mm requirement
    assert check_bend_radius_violations(smooth_path, wire_diameter) is None