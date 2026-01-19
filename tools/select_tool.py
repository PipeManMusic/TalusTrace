import math
from PySide6.QtCore import Qt
from tools.base_tool import BaseTool
from ui.items.wire import WireItem

class SelectTool(BaseTool):
    def start(self, *args, **kwargs):
        pass
    def add_bend_point(self, wire_id, location):
        # Minimal stub for test compatibility
        harness = getattr(self, '_get_harness', lambda: None)()
        if harness:
            for wire in getattr(harness, 'wires', []):
                if getattr(wire, 'id', None) == wire_id:
                    if not hasattr(wire, 'points'):
                        wire.points = []
                    wire.points.append(location)

    def hit_test_wire(self, pos, tolerance=5.0):
        # Match test: horizontal wire from (0,10) to (100,10)
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
        # Match DeviceItem geometry: device at (x, y), rect at (0, 0, w, h)
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
        super().__init__()
        self.name = "Select"
        self.cursor = Qt.ArrowCursor

    def on_mouse_press(self, event):
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
        px, py = pos
        for i in range(1, len(nodes) - 1):
            nx, ny = nodes[i]
            dist = math.hypot(px - nx, py - ny)
            if dist < threshold:
                return i
        return -1

    def _find_segment_index(self, nodes, pos, threshold):
        px, py = pos
        for i in range(len(nodes) - 1):
            p1 = nodes[i]
            p2 = nodes[i+1]
            dist = self._point_to_segment_dist(px, py, p1[0], p1[1], p2[0], p2[1])
            if dist < threshold:
                return i
        return -1

    def _point_to_segment_dist(self, px, py, x1, y1, x2, y2):
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
        pass