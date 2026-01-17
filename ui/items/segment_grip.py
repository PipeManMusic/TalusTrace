from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QBrush, QPen, QColor

class SegmentGripItem(QGraphicsRectItem):
    def __init__(self, wire_item, start_idx, end_idx, start_pos, end_pos, width=6.0, height=3.0):
        # Center grip between elbows
        mid_x = (start_pos[0] + end_pos[0]) / 2
        mid_y = (start_pos[1] + end_pos[1]) / 2
        super().__init__(-width/2, -height/2, width, height)
        self.setPos(QPointF(mid_x, mid_y))
        self.setBrush(QBrush(QColor(0, 200, 255)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, False)
        self.setZValue(1000)
        self.wire_item = wire_item
        self.start_idx = start_idx
        self.end_idx = end_idx

    def mouseMoveEvent(self, event):
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_move'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            print(f"[SegmentGripItem] Forwarding mouseMove to SegmentMoveTool with scene_pos={scene_pos}")
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_move(canvas_event)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.button() == Qt.LeftButton:
            print(f"[SegmentGripItem] Activating SegmentMoveTool for segment=({self.start_idx}, {self.end_idx})")
            from api.manager import APIManager
            api = APIManager.get_instance()
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            api.tool_manager.set_tool('segment_move', self.wire_item, self.start_idx, self.end_idx, canvas_event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        from api.manager import APIManager
        api = APIManager.get_instance()
        tool = api.tool_manager.active_tool
        if hasattr(tool, 'on_mouse_release'):
            from ui.utils import get_scene_pos
            scene_pos = get_scene_pos(event, api.input_system.canvas)
            print(f"[SegmentGripItem] Forwarding mouseRelease to SegmentMoveTool with scene_pos={scene_pos}")
            from ui.canvas import CanvasEvent
            canvas_event = CanvasEvent(event, scene_pos, api.input_system.canvas.scene if api.input_system.canvas else None)
            tool.on_mouse_release(canvas_event)
        event.accept()
