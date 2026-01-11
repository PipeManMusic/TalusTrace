from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QAction
from PySide6.QtCore import Qt, QLineF
from ui.coordinates import THEME_FALLBACK
from api.manager import APIManager
from api.actions import registry
import yaml
import os

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
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        
        self.context_menu_config = self._load_context_menu_config()

    def _load_context_menu_config(self):
        path = os.path.join("resources", "config", "ui_layout.yaml")
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get("context_menu", {})
        except: return {}

    def zoom_extents(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty():
            self.fitInView(rect, Qt.KeepAspectRatio)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu_type = None
        
        if item and hasattr(item, 'model'):
            type_name = type(item.model).__name__.lower()
            if type_name in self.context_menu_config:
                menu_type = type_name
        
        if not menu_type: return

        menu = QMenu(self)
        items = self.context_menu_config.get(menu_type, [])
        
        for entry in items:
            if entry.get("separator"):
                menu.addSeparator()
                continue
            
            cmd_id = entry.get("command")
            if cmd_id:
                label = cmd_id.split(".")[-1].replace("_", " ").title()
                action = QAction(label, self)
                action.triggered.connect(lambda chk=False, cid=cmd_id: registry.execute(cid))
                menu.addAction(action)
        
        menu.exec_(event.globalPos())

    def wheelEvent(self, event):
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
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake)
            return
        if event.button() == Qt.RightButton: return
        
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton: self.setDragMode(QGraphicsView.NoDrag)
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseReleaseEvent(event)

    def load_harness(self, harness):
        from ui.items import DeviceItem
        self.scene.clear()
        if not harness: return
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))

    def drawBackground(self, painter, rect):
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
