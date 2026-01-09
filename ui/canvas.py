from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent
from PySide6.QtCore import Qt, QLineF, QRectF
from ui.coordinates import THEME_FALLBACK
from api.manager import APIManager

class CanvasEvent:
    def __init__(self, view_event, scene_pos, scene, scene_item=None):
        self.original_event = view_event
        self.pos_mm = scene_pos
        self.scene = scene
        self.scene_item = scene_item

class HarnessCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # Anchors ensure zooming happens relative to cursor
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))

    def wheelEvent(self, event):
        """Restores standard zooming functionality."""
        zoom_in = event.angleDelta().y() > 0
        factor = 1.15 if zoom_in else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def _create_tool_event(self, event: QMouseEvent):
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        return CanvasEvent(event, scene_pos, self.scene, item)

    def mousePressEvent(self, event):
        """Fixes panning/tool conflict and restores dragging."""
        if event.button() == Qt.MiddleButton:
            # Enable panning for middle button
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Create a fake left-click so Qt starts the scroll-hand logic
            fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake_event)
            return

        if event.button() == Qt.RightButton:
            self.show_context_menu(event.position().toPoint())
            return
            
        # Dispatch to Tool System (Select/Placement)
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        
        # Relay to super() to allow ItemIsMovable logic for Left-Click
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Allows standard Qt item movement while notifying tools."""
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Cleans up panning and release states."""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        super().mouseReleaseEvent(event)

    def load_harness(self, harness):
        """Unified factory for creating visuals."""
        from ui.items import DeviceItem
        self.scene.clear()
        if not harness: return
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))

    def drawBackground(self, painter, rect):
        """Renders the 25mm engineering grid."""
        super().drawBackground(painter, rect)
        grid_pen = QPen(QColor(THEME_FALLBACK["grid_color"]))
        grid_pen.setWidth(0)
        painter.setPen(grid_pen)
        grid_size = 25.0
        left = int(rect.left()) - (int(rect.left()) % int(grid_size))
        top = int(rect.top()) - (int(rect.top()) % int(grid_size))
        lines = []
        for x in range(left, int(rect.right()), int(grid_size)):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), int(grid_size)):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.drawLines(lines)