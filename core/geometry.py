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


def snap_to_grid_mm(value_mm: float, grid_step_mm: float) -> float:
    """
    Rounds a mm value to the nearest grid step (orthogonal snapping).
    Example: grid_step_mm=2.0 snaps to nearest multiple of 2.0mm.
    """
    return round(value_mm / grid_step_mm) * grid_step_mm


# PH2-2.1: SpatialHasher for wire segment hashing
class SpatialHasher:
    def __init__(self, grid_size: float = 2.0):
        self.grid_size = grid_size

    def get_key(self, segment):
        """
        Returns a hashable key for a wire segment, snapped to grid.
        Segment: ((x1, y1), (x2, y2))
        """
        (x1, y1), (x2, y2) = segment
        gx1 = round(x1 / self.grid_size)
        gy1 = round(y1 / self.grid_size)
        gx2 = round(x2 / self.grid_size)
        gy2 = round(y2 / self.grid_size)
        # Order-independent key for segment
        return tuple(sorted([(gx1, gy1), (gx2, gy2)]))
