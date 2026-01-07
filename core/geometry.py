# PH3-2.1: Procedural Helix Sine Wave Logic
import math

def generate_helix_points(path, amplitude=2.0, pitch=5.0, num_points=20):
    """
    Generates two sets of helix points (A, B) offset by sine/cosine along the normal of the path.
    path: list of (x, y) tuples (mm)
    amplitude: float, helix amplitude (mm)
    pitch: float, helix pitch (mm)
    num_points: int, number of points to generate
    Returns: (helix_a, helix_b) as lists of (x, y) tuples
    """
    if len(path) < 2:
        raise ValueError("Path must have at least two points")
    # For simplicity, treat as straight segment from path[0] to path[-1]
    x0, y0 = path[0]
    x1, y1 = path[-1]
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return [path[0]], [path[0]]
    # Unit tangent
    tx = dx / length
    ty = dy / length
    # Unit normal (perpendicular)
    nx = -ty
    ny = tx
    helix_a = []
    helix_b = []
    for i in range(num_points + 1):
        t = (i / num_points) * length
        # Sine/cosine offset for helix
        offset_a = amplitude * math.sin(2 * math.pi * t / pitch)
        offset_b = amplitude * math.cos(2 * math.pi * t / pitch)
        # Base point along path
        px = x0 + tx * t
        py = y0 + ty * t
        # Offset by normal
        ax = px + nx * offset_a
        ay = py + ny * offset_a
        bx = px + nx * offset_b
        by = py + ny * offset_b
        helix_a.append((ax, ay))
        helix_b.append((bx, by))
    return helix_a, helix_b
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
