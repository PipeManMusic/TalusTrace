
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
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
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

    def mouseMoveEvent(self, event):
        """Handle mouse movement to move both elbows and update the wire segment in real time."""
        # Move both elbows by the delta of the mouse movement
        delta = event.scenePos() - event.lastScenePos()
        self.wire_item.path_nodes[self.start_idx][0] += delta.x()
        self.wire_item.path_nodes[self.start_idx][1] += delta.y()
        self.wire_item.path_nodes[self.end_idx][0] += delta.x()
        self.wire_item.path_nodes[self.end_idx][1] += delta.y()
        # Rebuild grips so segment grips follow in real time
        self.wire_item._build_path_and_grips()
        self.wire_item.notify_observers('geometry_changed')
        self.wire_item.update()
        # Forward to tool if needed
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos2 = get_scene_pos(event, api.input_system.canvas)
            # ...removed debug print...
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos2, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()



