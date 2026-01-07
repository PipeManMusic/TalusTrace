import pytest
import math
from core.geometry import calculate_bundle_diameter

def test_bundle_diameter_standard_calc():
    """
    Validates the Bundle Diameter Algorithm (Spec 2.2):
    D = 1.15 * sqrt(sum(d^2))
    """
    # Test Case 1: Single wire of diameter 2mm
    # Calculation: 1.15 * sqrt(2^2) = 1.15 * 2 = 2.3
    assert calculate_bundle_diameter([2.0]) == pytest.approx(2.3)

    # Test Case 2: Four wires of diameter 1mm
    # Calculation: 1.15 * sqrt(1^2 + 1^2 + 1^2 + 1^2) 
    # = 1.15 * sqrt(4) = 1.15 * 2 = 2.3
    wire_diameters = [1.0, 1.0, 1.0, 1.0]
    expected = 1.15 * math.sqrt(sum(d**2 for d in wire_diameters))
    assert calculate_bundle_diameter(wire_diameters) == pytest.approx(expected)

def test_bundle_diameter_empty():
    """Ensures empty bundles return 0 diameter."""
    assert calculate_bundle_diameter([]) == 0.0

def test_bundle_diameter_precision():
    """Validates algorithm with mixed industrial gauges."""
    # Mixed gauges: 0.5mm, 1.5mm, 2.0mm
    gauges = [0.5, 1.5, 2.0]
    # sum(d^2) = 0.25 + 2.25 + 4.0 = 6.5
    expected = 1.15 * math.sqrt(6.5) # ~2.931
    assert calculate_bundle_diameter(gauges) == pytest.approx(expected, rel=1e-4)