import math
from typing import List

def calculate_bundle_diameter(wire_diameters: List[float]) -> float:
    """
    Calculates the bundle diameter according to Spec 2.2:
    D = 1.15 * sqrt(sum(d^2))
    Returns 0.0 for empty input.
    """
    if not wire_diameters:
        return 0.0
    return 1.15 * math.sqrt(sum(d ** 2 for d in wire_diameters))
