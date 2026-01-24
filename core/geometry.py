"""
Geometry utilities for Talus Trace: helix generation, bundle diameter calculation, grid snapping, and spatial hashing.
Implements procedural wire logic and grid-based segment hashing.
"""
# PH3-2.1: Procedural Helix Sine Wave Logic
import math
from typing import List

def generate_helix_points(path, amplitude=2.0, pitch=5.0, num_points=200):
    """
    Generates two sets of helix points (A, B) offset by sine logic along the normal.
    Corrected: Wires are exactly 180 degrees out of phase (opposite).
    """
    if len(path) < 2:
        raise ValueError("Path must have at least two points")
        
    # For a simple segment; for multi-segment paths, this would iterate segments
    x0, y0 = path[0]
    x1, y1 = path[-1]
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    
    if length == 0:
        return [path[0]], [path[0]]
        
    # Unit tangent and normal
    tx, ty = dx / length, dy / length
    nx, ny = -ty, tx
    
    helix_a = []
    helix_b = []
    
    for i in range(num_points + 1):
        t = (i / num_points) * length
        
        # Calculate angle based on pitch
        angle = 2 * math.pi * t / pitch
        
        # Wire A uses Sine
        offset_a = amplitude * math.sin(angle)
        
        # Wire B uses Negative Sine for 180-degree phase shift (Opposite)
        offset_b = -offset_a 
        
        # Base point along path
        px = x0 + tx * t
        py = y0 + ty * t
        
        # Offset by normal
        helix_a.append((px + nx * offset_a, py + ny * offset_a))
        helix_b.append((px + nx * offset_b, py + ny * offset_b))
        
    return helix_a, helix_b

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
    """
    return round(value_mm / grid_step_mm) * grid_step_mm

# PH2-2.1: SpatialHasher for wire segment hashing
class SpatialHasher:
    """
    Provides grid-based hashing for wire segments to enable fast spatial queries.
    """
    def __init__(self, grid_size: float = 2.0):
        """
        Initialize the SpatialHasher with a grid size.
        Args:
            grid_size (float): Grid size in mm for hashing.
        """
        self.grid_size = grid_size

    def get_key(self, segment):
        """
        Returns a hashable key for a wire segment, snapped to grid.
        Args:
            segment (tuple): ((x1, y1), (x2, y2)) coordinates of the segment.
        Returns:
            tuple: Grid-snapped coordinates as a hashable key.
        """
        (x1, y1), (x2, y2) = segment
        gx1 = round(x1 / self.grid_size)
        gy1 = round(y1 / self.grid_size)
        gx2 = round(x2 / self.grid_size)
        gy2 = round(y2 / self.grid_size)
        return tuple(sorted([(gx1, gy1), (gx2, gy2)]))