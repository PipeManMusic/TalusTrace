"""
Elbow grip item for Talus Trace UI.

Provides a draggable handle for wire elbows in the scene.
"""

from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor

from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin

class ElbowGripItem(ObservableGraphicsItemMixin, QGraphicsEllipseItem):
    """Draggable handle for wire elbows, supporting geometry updates and tool integration."""
    _interactive_grip = True
    __test_scenario__ = {
        'model_data': {'index': 0, 'pos': (0, 0)},
        'expected_child_count': 0
    }
    def __init__(self, wire_item, index, pos, radius=2.5, parent=None):
        """Initialize ElbowGripItem with wire reference, index, position, and radius."""
        QGraphicsEllipseItem.__init__(self, -radius, -radius, radius*2, radius*2, parent)
        self._observers = []
        self.setPos(QPointF(pos[0], pos[1]))
        self.setBrush(QBrush(QColor(255, 200, 0)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, False)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsEllipseItem.ItemIsFocusable, False)
        self.setAcceptHoverEvents(True)
        self.setZValue(2000)
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.wire_item = wire_item
        self.index = index
        self.radius = radius
        self._drag_start_pos = None

    def mousePressEvent(self, event):
        """Record the starting position for undo on drag start."""
        if event.button() == Qt.LeftButton:
            nodes = self.wire_item.path_nodes
            if 0 <= self.index < len(nodes):
                self._drag_start_pos = list(nodes[self.index])
                # Track raw (unsnapped) position so small deltas accumulate
                self._raw_pos = list(nodes[self.index])
        event.accept()

    def _snap(self, x, y):
        """Snap coordinates to the grid."""
        from api.manager import APIManager
        api = APIManager.get_instance()
        if hasattr(api, 'settings') and hasattr(api.settings, 'snap'):
            return api.settings.snap(x), api.settings.snap(y)
        return x, y

    def mouseMoveEvent(self, event):
        """Update model path_nodes directly during drag for real-time feedback."""
        delta = event.scenePos() - event.lastScenePos()
        nodes = self.wire_item.path_nodes
        if 0 <= self.index < len(nodes):
            # Accumulate raw position so small deltas aren't lost to snapping
            self._raw_pos[0] += delta.x()
            self._raw_pos[1] += delta.y()
            sx, sy = self._snap(self._raw_pos[0], self._raw_pos[1])
            nodes[self.index][0] = sx
            nodes[self.index][1] = sy
            self.setPos(QPointF(sx, sy))
            self.wire_item._rebuild_path()
            # Sync segment grips to updated node positions
            for sg in self.wire_item.segment_grips:
                if len(nodes) > max(sg.start_idx, sg.end_idx):
                    mx = (nodes[sg.start_idx][0] + nodes[sg.end_idx][0]) / 2
                    my = (nodes[sg.start_idx][1] + nodes[sg.end_idx][1]) / 2
                    sg.setPos(QPointF(mx, my))
            self.wire_item.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        """Commit the move as a single undoable command."""
        if event.button() == Qt.LeftButton and self._drag_start_pos is not None:
            nodes = self.wire_item.path_nodes
            new_pos = list(nodes[self.index]) if 0 <= self.index < len(nodes) else None
            if new_pos and self._drag_start_pos != new_pos:
                from api.manager import APIManager
                api = APIManager.get_instance()
                from tools.elbow_move_tool import MoveElbowCommand
                cmd = MoveElbowCommand(
                    self.wire_item.model, self.index,
                    self._drag_start_pos, new_pos, api=api
                )
                # execute() sets absolute pos (idempotent), safe to re-execute
                api.context.undo_stack.push(cmd)
            self._drag_start_pos = None
        super().mouseReleaseEvent(event)

