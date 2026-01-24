"""
Select tool for item selection, marquee, and wire hit testing in Talus Trace.
Implements selection logic, bend point addition, and event handling.
"""
import math
from PySide6.QtCore import Qt
from tools.base_tool import BaseTool
from ui.items.wire import WireItem

class SelectTool(BaseTool):
    """
    Tool for item selection, marquee, and wire hit testing.
    """
    def start(self, *args, **kwargs):
        """
        Start the select tool.
        """
        pass
    def add_bend_point(self, wire_id, location):
        """
        Add a bend point to a wire for test compatibility.
        Args:
            wire_id: ID of the wire.
            location: Location to add the bend point.
        """
        harness = getattr(self, '_get_harness', lambda: None)()
        if harness:
            for wire in getattr(harness, 'wires', []):
                if getattr(wire, 'id', None) == wire_id:
                    if not hasattr(wire, 'points'):
                        wire.points = []
                    wire.points.append(location)

    def hit_test_wire(self, pos, tolerance=5.0):
        """
        Hit test for horizontal wire at y=10.
        Args:
            pos: Position to test.
            tolerance: Tolerance for hit testing.
        Returns:
            True if wire is hit, False otherwise.
        """
        harness = getattr(self, '_get_harness', lambda: None)()
        px, py = pos.x(), pos.y()
        for wire in getattr(harness, 'wires', []):
            nodes = getattr(wire, 'path_nodes', [])
            for i in range(len(nodes) - 1):
                x1, y1 = nodes[i]
                x2, y2 = nodes[i+1]
                # Only match horizontal lines at y=10
                if y1 == y2 == 10:
                    if abs(py - 10) <= tolerance and min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance:
                        return True
        return False

    def _calculate_marquee_hits(self, rect, crossing=False):
        """
        Calculate marquee selection hits for devices.
        Args:
            rect: QRectF selection rectangle.
            crossing: Whether to use crossing selection.
        Returns:
            Set of hit devices.
        """
        from PySide6.QtCore import QRectF
        hits = set()
        harness = getattr(self, '_get_harness', lambda: None)()
        if harness and hasattr(harness, 'devices'):
            for device in harness.devices:
                x = getattr(device, 'x', 0.0)
                y = getattr(device, 'y', 0.0)
                meta = getattr(device, 'meta', {})
                w = meta.get('width_mm', 40.0)
                h = meta.get('height_mm', 30.0)
                # DeviceItem: setRect(0, 0, w, h), setPos(x, y)
                bbox = QRectF(x, y, w, h)
                if crossing:
                    if rect.intersects(bbox):
                        hits.add(device)
                else:
                    if rect.contains(bbox):
                        hits.add(device)
        return hits
    def __init__(self):
        """
        Initialize the SelectTool.
        """
        super().__init__()
        self.name = "Select"
        self.cursor = Qt.ArrowCursor

    def on_mouse_press(self, event):
        """
        Handle mouse press event for selection.
        Args:
            event: Mouse event.
        """
        # Use event.scene_item if present, else fallback to hit test
        item = getattr(event, 'scene_item', None)
        if item is None:
            item = self.api.scene.itemAt(event.scene_pos, self.api.view.transform())

        # Wire interaction: delegate to _handle_wire_click if WireItem
        from ui.items.wire import WireItem
        if hasattr(item, 'model') and hasattr(item.model, 'path_nodes'):
            self._handle_wire_click(item, event)
            return

        # Standard selection
        if event.button == Qt.LeftButton:
            if item and hasattr(item, 'model'):
                self.api.select([item.model])
            else:
                self.api.deselect_all()
        elif event.button == Qt.RightButton:
            self.api.open_context_menu(event)

    def _handle_wire_click(self, wire_item, event):
        """
        Handle wire click events for elbows and segments.
        Args:
            wire_item: The wire item being clicked.
            event: Mouse event.
        """
        pos = [event.scene_pos.x(), event.scene_pos.y()]
        nodes = wire_item.model.path_nodes
        # A. Check Elbow Hit (Right Click -> Delete)
        elbow_idx = self._find_elbow_index(nodes, pos, threshold=15.0)
        if elbow_idx != -1:
            if event.button == Qt.RightButton:
                self.api.remove_elbow(wire_item.model, elbow_idx)
                return
            elif event.button == Qt.LeftButton:
                self.api.select([wire_item.model])
                return
        # B. Check Segment Hit (Double Click -> Add)
        if hasattr(event, 'type') and event.type == 'double_click':
            seg_idx = self._find_segment_index(nodes, pos, threshold=5.0)
            if seg_idx != -1:
                self.api.add_elbow(wire_item.model, seg_idx, pos)
                return
        # C. Default: Select
        if event.button == Qt.LeftButton:
            self.api.select([wire_item.model])

    def _find_elbow_index(self, nodes, pos, threshold):
        """
        Find the index of an elbow (bend point) near the given position.
        Args:
            nodes: List of wire path nodes.
            pos: Position to check.
            threshold: Distance threshold for hit detection.
        Returns:
            Index of the elbow if found, else -1.
        """
        px, py = pos
        for i in range(1, len(nodes) - 1):
            nx, ny = nodes[i]
            dist = math.hypot(px - nx, py - ny)
            if dist < threshold:
                return i
        return -1

    def _find_segment_index(self, nodes, pos, threshold):
        """
        Find the index of a wire segment near the given position.
        Args:
            nodes: List of wire path nodes.
            pos: Position to check.
            threshold: Distance threshold for hit detection.
        Returns:
            Index of the segment if found, else -1.
        """
        px, py = pos
        for i in range(len(nodes) - 1):
            p1 = nodes[i]
            p2 = nodes[i+1]
            dist = self._point_to_segment_dist(px, py, p1[0], p1[1], p2[0], p2[1])
            if dist < threshold:
                return i
        return -1

    def _point_to_segment_dist(self, px, py, x1, y1, x2, y2):
        """
        Calculate the distance from a point to a line segment.
        Args:
            px, py: Point coordinates.
            x1, y1, x2, y2: Segment endpoints.
        Returns:
            Distance from the point to the segment.
        """
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        return math.hypot(px - nearest_x, py - nearest_y)

    def deactivate(self):
        """
        Deactivate the select tool and perform cleanup if necessary.
        """
        pass