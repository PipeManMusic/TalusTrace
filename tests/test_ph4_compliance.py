import pytest
from core.logic import check_bend_radius_violations

def test_ph4_3_2_bend_radius_violation():
    wire_diameter = 2.0
    sharp_path = [(0,0), (2,0), (2,2)]
    
    violation = check_bend_radius_violations(sharp_path, wire_diameter)
    
    # REFACTOR: Use object attributes
    assert violation is not None
    assert "BEND_RADIUS" in violation.category
    assert violation.severity == "ERROR"

def test_ph4_3_2_compliant_bend():
    wire_diameter = 2.0
    smooth_path = [(0,0), (20,0), (20,20)]
    assert check_bend_radius_violations(smooth_path, wire_diameter) is None
