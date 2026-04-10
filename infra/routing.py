"""
Routing engine for automated netlist-to-routing in Talus Trace.
Generates orthogonal paths and updates wire routing on the engineering grid.
"""
from core.harness import Harness
from typing import Tuple, List

class RoutingEngine:
    """
    PH4-2.1: Automated Netlist-to-Routing Engine.
    Generates orthogonal paths on the 2.0mm 'Holy Millimeter' grid.
    """
    def __init__(self, harness: Harness):
        """
        Initialize the RoutingEngine with a harness and grid size.
        Args:
            harness: Harness object containing devices and wires.
        """
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

    def route_all_wires(self, api=None):
        """
        Updates every wire in the harness based on source/target pin IDs.
        Optionally accepts an APIManager to dispatch model_changed events.
        """
        wires = self.harness.wires
        # Support both list and dict-style wire collections
        wire_iter = wires.values() if hasattr(wires, 'values') else wires
        for wire in wire_iter:
            src_pin = self.harness.pin_map.get(wire.from_conn)
            tgt_pin = self.harness.pin_map.get(wire.to_conn)
            if src_pin and tgt_pin:
                wire.path_nodes = self.compute_orthogonal_path(src_pin.head, tgt_pin.head)
                if api is not None:
                    api.dispatch("model_changed", {"action": "update", "item": wire})
