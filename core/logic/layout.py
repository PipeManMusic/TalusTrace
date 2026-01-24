"""
Layout logic for Talus Trace.
Handles device and wire layout algorithms.
"""

import math
from typing import List, Tuple
from .base import iter_segments

# PH2-3.2: Core: Calculate Label MM Position from T-Pos
def calculate_label_mm_position(nodes: List[Tuple[float, float]], t: float) -> Tuple[float, float]:
    """
    Interpolates the mm position along a multi-segment wire (Spec 5).
    """
    if not nodes or len(nodes) < 2:
        raise ValueError("Wire must have at least two nodes")
    
    # Use shared iterator from base.py
    segments = list(iter_segments(nodes))
    lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in segments]
    total_length = sum(lengths)
    
    if total_length == 0:
        return nodes[0]
    
    target_length = t * total_length
    acc = 0.0
    for idx, seg_len in enumerate(lengths):
        if acc + seg_len >= target_length:
            a, b = segments[idx]
            seg_t = (target_length - acc) / seg_len if seg_len > 0 else 0.0
            x = a[0] + (b[0] - a[0]) * seg_t
            y = a[1] + (b[1] - a[1]) * seg_t
            return (x, y)
        acc += seg_len
    return nodes[-1]