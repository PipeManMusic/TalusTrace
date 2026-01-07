import pytest
import math
from core.logic import calculate_bundle_diameter

def test_bundle_sizing_accuracy():
    """
    Validates PH3-1.2: Core: Implement Industrial Packing Factor Calculation.
    Uses D = 1.15 * sqrt(sum d^2) for sizing.
    """
    # Test 1: Single wire (Diameter should essentially be the wire diameter * packing factor)
    # 1.15 * sqrt(3^2) = 3.45
    assert calculate_bundle_diameter([3.0]) == pytest.approx(3.45, 0.01)

    # Test 2: Multiple wires (e.g., 5 wires of 1.0mm)
    # 1.15 * sqrt(1^2 + 1^2 + 1^2 + 1^2 + 1^2) = 1.15 * 2.236 = 2.57
    diameters = [1.0, 1.0, 1.0, 1.0, 1.0]
    assert calculate_bundle_diameter(diameters) == pytest.approx(2.57, 0.01)