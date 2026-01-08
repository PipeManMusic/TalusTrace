from typing import Optional
from core.models import Wire
import math

class BOMGenerator:
    """
    PH5-1.1: Automated BOM & Cut-List Generator
    Calculates true cut-lengths for wires, including twist factor and slack.
    """
    def __init__(self, harness: Optional[object] = None):
        self.harness = harness

    def calculate_cut_length(self, wire: Wire) -> float:
        """
        Returns the manufacturing cut length for a wire:
        - Standard: sum of segment lengths + 50mm slack
        - Twisted Pair: sum * 1.05 (twist factor) + 50mm slack
        """
        nodes = getattr(wire, 'path_nodes', [])
        if not nodes or len(nodes) < 2:
            return 0.0
        total_length = 0.0
        for i in range(len(nodes) - 1):
            a, b = nodes[i], nodes[i+1]
            total_length += math.hypot(b[0] - a[0], b[1] - a[1])
        slack = 50.0
        if getattr(wire, 'type', None) == 'TWISTED_PAIR':
            return round(total_length * 1.05 + slack, 1)
        return round(total_length + slack, 1)
