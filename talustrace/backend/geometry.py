import math
from typing import Tuple, List

def calculate_double_helix(
    start: Tuple[float, float],
    end: Tuple[float, float],
    amplitude: float,
    wavelength: float,
    phase_offset: float = 0.0
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    x0, y0 = start
    x1, y1 = end
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0 or amplitude == 0 or wavelength == 0:
        return [], []
    angle = math.atan2(dy, dx)
    # Perpendicular angle
    perp_angle = angle + math.pi / 2
    # Step size: finer for smoother helix
    step_size = max(wavelength / 10.0, 1.0)
    num_steps = max(int(length / step_size), 2)
    strand1 = []
    strand2 = []
    for i in range(num_steps + 1):
        t = i * length / num_steps
        # Position along the main line
        px = x0 + (dx * t / length)
        py = y0 + (dy * t / length)
        # Sine/cosine offset for each strand
        offset1 = amplitude * math.sin((2 * math.pi * t / wavelength) + phase_offset)
        offset2 = amplitude * math.sin((2 * math.pi * t / wavelength) + phase_offset + math.pi)
        # Perpendicular offsets
        ox1 = offset1 * math.cos(perp_angle)
        oy1 = offset1 * math.sin(perp_angle)
        ox2 = offset2 * math.cos(perp_angle)
        oy2 = offset2 * math.sin(perp_angle)
        strand1.append((px + ox1, py + oy1))
        strand2.append((px + ox2, py + oy2))
    # Ensure start and end points are exact
    strand1[0] = start
    strand1[-1] = end
    strand2[0] = start
    strand2[-1] = end
    return strand1, strand2
