
"""
Segment grip item for Talus Trace UI.

Provides a movable grip for wire segments, allowing interactive editing of wire geometry.
"""

from PySide6.QtWidgets import QGraphicsRectItem
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor


class SegmentGripItem(ObservableGraphicsItemMixin, QGraphicsRectItem):
    """Movable grip for a wire segment, allowing interactive geometry editing."""
    _interactive_grip = True
    __test_scenario__ = {
        'model_data': {'start_idx': 0, 'end_idx': 1, 'start_pos': (0, 0), 'end_pos': (1, 1)},
        'expected_child_count': 0
    }
    def __init__(self, wire_item, start_idx, end_idx, start_pos, end_pos, width=6.0, height=3.0, parent=None):
        """Initialize a SegmentGripItem between two elbows of a wire segment."""
        # Center grip between elbows
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        QGraphicsRectItem.__init__(self, -width/2, -height/2, width, height, parent)
        self._observers = []
        self.setPos(QPointF(mid_x, mid_y))
        self.setBrush(QBrush(QColor(0, 200, 255)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        self.setZValue(1000)
        self.wire_item = wire_item
        self.start_idx = start_idx
        self.end_idx = end_idx
        # Subscribe to wire geometry changes
        if hasattr(self.wire_item, 'subscribe'):
            self.wire_item.subscribe('geometry_changed', self._on_wire_geometry_changed)

    def _on_wire_geometry_changed(self, *args, **kwargs):
        """Update the grip position when the wire geometry changes."""
        # Use the wire model's path_nodes if available for real-time updates
        path_nodes = None
        if hasattr(self.wire_item, 'model') and hasattr(self.wire_item.model, 'path_nodes'):
            path_nodes = self.wire_item.model.path_nodes
        elif hasattr(self.wire_item, 'path_nodes'):
            path_nodes = self.wire_item.path_nodes
        if path_nodes and len(path_nodes) > max(self.start_idx, self.end_idx):
            start = path_nodes[self.start_idx]
            end = path_nodes[self.end_idx]
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2
            self.setPos(QPointF(mid_x, mid_y))

    def _can_move_any_node(self):
        """Return True if at least one of the two nodes is an interior node."""
        num = len(self.wire_item.path_nodes)
        return (0 < self.start_idx < num - 1) or (0 < self.end_idx < num - 1)

    def _snap(self, x, y):
        """Snap coordinates to the grid."""
        from api.manager import APIManager
        api = APIManager.get_instance()
        if hasattr(api, 'settings') and hasattr(api.settings, 'snap'):
            return api.settings.snap(x), api.settings.snap(y)
        return x, y

    def mousePressEvent(self, event):
        """Record starting positions for undo."""
        if event.button() == Qt.LeftButton:
            if not self._can_move_any_node():
                event.ignore()
                return
            nodes = self.wire_item.path_nodes
            if len(nodes) > max(self.start_idx, self.end_idx):
                self._start_positions = (
                    list(nodes[self.start_idx]),
                    list(nodes[self.end_idx]),
                )
                # Track raw (unsnapped) positions so small deltas accumulate
                self._raw_start = list(nodes[self.start_idx])
                self._raw_end = list(nodes[self.end_idx])
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement to move both nodes and update the wire segment in real time."""
        if not self._can_move_any_node():
            event.ignore()
            return
        delta = event.scenePos() - event.lastScenePos()
        nodes = self.wire_item.path_nodes
        num_nodes = len(nodes)
        if num_nodes > max(self.start_idx, self.end_idx):
            # Only move interior nodes — endpoints (index 0 and last) are
            # anchored to connected pins and must not be dragged away.
            if 0 < self.start_idx < num_nodes - 1:
                self._raw_start[0] += delta.x()
                self._raw_start[1] += delta.y()
                sx, sy = self._snap(self._raw_start[0], self._raw_start[1])
                nodes[self.start_idx][0] = sx
                nodes[self.start_idx][1] = sy
            if 0 < self.end_idx < num_nodes - 1:
                self._raw_end[0] += delta.x()
                self._raw_end[1] += delta.y()
                sx, sy = self._snap(self._raw_end[0], self._raw_end[1])
                nodes[self.end_idx][0] = sx
                nodes[self.end_idx][1] = sy
        # Update visuals without rebuilding grips (avoids removing self mid-drag)
        self.wire_item._rebuild_path()
        # Position this grip at the midpoint of its two nodes
        mx = (nodes[self.start_idx][0] + nodes[self.end_idx][0]) / 2
        my = (nodes[self.start_idx][1] + nodes[self.end_idx][1]) / 2
        self.setPos(QPointF(mx, my))
        # Sync elbow grips to their new model positions
        for grip in self.wire_item.elbow_grips:
            if 0 <= grip.index < len(nodes):
                grip.setPos(QPointF(nodes[grip.index][0], nodes[grip.index][1]))
        # Sync other segment grips positions
        for sg in self.wire_item.segment_grips:
            if sg is self:
                continue
            if len(nodes) > max(sg.start_idx, sg.end_idx):
                mx = (nodes[sg.start_idx][0] + nodes[sg.end_idx][0]) / 2
                my = (nodes[sg.start_idx][1] + nodes[sg.end_idx][1]) / 2
                sg.setPos(QPointF(mx, my))
        self.wire_item.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        """Commit the segment move as a single undoable command."""
        if event.button() == Qt.LeftButton and hasattr(self, '_start_positions') and self._start_positions is not None:
            from api.manager import APIManager
            api = APIManager.get_instance()
            nodes = self.wire_item.path_nodes
            num_nodes = len(nodes)
            old_start, old_end = self._start_positions
            new_start = list(nodes[self.start_idx])
            new_end = list(nodes[self.end_idx])
            # Only interior nodes can move; endpoints stay pinned
            start_moved = (0 < self.start_idx < num_nodes - 1) and old_start != new_start
            end_moved = (0 < self.end_idx < num_nodes - 1) and old_end != new_end
            if start_moved or end_moved:
                if start_moved:
                    dx = new_start[0] - old_start[0]
                    dy = new_start[1] - old_start[1]
                else:
                    dx = new_end[0] - old_end[0]
                    dy = new_end[1] - old_end[1]
                # Undo back to old positions for moved nodes
                if start_moved:
                    nodes[self.start_idx] = old_start
                if end_moved:
                    nodes[self.end_idx] = old_end
                from tools.segment_move_tool import MoveSegmentCommand
                cmd = MoveSegmentCommand(
                    self.wire_item.model, self.start_idx, self.end_idx,
                    dx, dy, api
                )
                api.context.undo_stack.push(cmd)
            self._start_positions = None
        super().mouseReleaseEvent(event)



