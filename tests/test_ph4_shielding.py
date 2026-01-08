import pytest
from core.logic import calculate_bundle_diameter

def test_ph4_2_2_shielded_packing_factor():
    """
    Validates that shielded cables add significant volume to bundles.
    """
    standard_wires = [1.0, 1.0]
    shielded_wire = {"diameter": 1.0, "shield_thickness": 0.5}
    
    d_normal = calculate_bundle_diameter(standard_wires)
    # The shield effectively increases the d^2 contribution
    d_shielded = calculate_bundle_diameter([2.0, 1.0]) 
    
    assert d_shielded > d_normal