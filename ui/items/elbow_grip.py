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
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2000)  # Ensure it's above the wire and other items
        self.setAcceptedMouseButtons(Qt.LeftButton | Qt.RightButton)
        self.wire_item = wire_item
        self.index = index
        self.radius = radius
        # Subscribe to wire geometry changes
        if hasattr(self.wire_item, 'subscribe'):
            self.wire_item.subscribe('geometry_changed', self._on_wire_geometry_changed)

    def _on_wire_geometry_changed(self, *args, **kwargs):
        """Update position to match wire's current node and trigger wire repaint."""
        # Update position to match wire's current node
        if hasattr(self.wire_item, 'path_nodes') and len(self.wire_item.path_nodes) > self.index:
            pos = self.wire_item.path_nodes[self.index]
            self.setPos(QPointF(pos[0], pos[1]))
        # Force wire to repaint so blue dot follows elbow in real time
        if hasattr(self.wire_item, 'update'):
            self.wire_item.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move events, updating elbow position and forwarding to active tool."""
        # Route elbow move through APIManager
        scene_pos = event.scenePos()
        from api.manager import APIManager
        api = APIManager.get_instance()
        api.move_elbow(self.wire_item.model, self.index, [scene_pos.x(), scene_pos.y()])
        # Forward to tool if needed
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos2 = get_scene_pos(event, api.input_system.canvas)
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos2, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events, updating elbow position and forwarding to active tool."""
        # ...removed debug print...
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            # ...removed debug print...
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()



