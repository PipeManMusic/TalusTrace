from core.harness import Harness
from typing import Tuple, List

class RoutingEngine:
    """
    PH4-2.1: Automated Netlist-to-Routing Engine.
    Generates orthogonal paths on the 2.0mm 'Holy Millimeter' grid.
    """
    def __init__(self, harness: Harness):
        self.harness = harness
        self.grid_size = 2.0

    def compute_orthogonal_path(self, start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Generates a simple Manhattan/Orthogonal path between two points.
        Ensures all points are snapped to the engineering grid.
        """
        x1, y1 = start
        x2, y2 = end
        # Simple L-shape route (Horizontal then Vertical)
        # In a full implementation, this would avoid collisions using SpatialHash
        mid_point = (x2, y1)
        path = [start, mid_point, end]
        # Snap all nodes to the 2.0mm grid (PH2-1.1)
        return [(round(x / self.grid_size) * self.grid_size, 
                 round(y / self.grid_size) * self.grid_size) for x, y in path]

    def route_all_wires(self):
        """
        Updates every wire in the harness meta based on source/target pin IDs.
        """
        for wire in self.harness.wires.values():
            src_pin = self.harness.pin_map.get(wire.source_pin_id)
            tgt_pin = self.harness.pin_map.get(wire.target_pin_id)
            if src_pin and tgt_pin:
                wire.path_nodes = self.compute_orthogonal_path(src_pin.head, tgt_pin.head)
