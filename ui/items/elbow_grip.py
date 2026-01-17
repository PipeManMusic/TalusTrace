from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor

class ElbowGripItem(QGraphicsEllipseItem):
    def __init__(self, wire_item, index, pos, radius=2.5):
        super().__init__(-radius, -radius, radius*2, radius*2)
        self.setPos(QPointF(pos[0], pos[1]))
        self.setBrush(QBrush(QColor(255, 200, 0)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, False)
        self.setZValue(1000)
        self.wire_item = wire_item
        self.index = index
        self.radius = radius

    def mouseMoveEvent(self, event):
        print(f"[ElbowGripItem] mouseMoveEvent: index={self.index}, pos={event.scenePos()}")
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            print(f"[ElbowGripItem] Forwarding mouseMove to ElbowMoveTool with scene_pos={scene_pos}")
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()

    def mouseMoveEvent(self, event):
        print(f"[ElbowGripItem] mouseMoveEvent: index={self.index}, pos={event.scenePos()}")
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            print(f"[ElbowGripItem] Forwarding mouseMove to ElbowMoveTool with scene_pos={scene_pos}")
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()

    def mouseReleaseEvent(self, event):
        print(f"[ElbowGripItem] mouseReleaseEvent: index={self.index}, pos={event.scenePos()}")
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_release'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            print(f"[ElbowGripItem] Forwarding mouseRelease to ElbowMoveTool with scene_pos={scene_pos}")
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_release(canvas_event)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        # No-op for double click on grip
        event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.wire_item.delete_elbow(self.index)
            event.accept()
        elif event.button() == Qt.LeftButton:
            print(f"[ElbowGripItem] Activating ElbowMoveTool for index={self.index}")
            from api.manager import APIManager
            api = APIManager.get_instance()
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            api.tool_manager.set_tool('elbow_move', self.wire_item, self.index, canvas_event)
            event.accept()
        else:
            super().mousePressEvent(event)
