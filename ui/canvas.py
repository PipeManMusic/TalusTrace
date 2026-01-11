import math
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
        self.api = APIManager.get_instance()
        
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
        self.api.subscribe("model_changed", self.refresh)

    def refresh(self, data):
        self.load_harness(self.api.context.harness)

    def _load_context_menu_config(self):
        path = os.path.join("resources", "config", "ui_layout.yaml")
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get("context_menu", {})
        except: return {}

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu_type = None
        if item and hasattr(item, 'model'):
            menu_type = type(item.model).__name__.lower()
        
        if not menu_type or menu_type not in self.context_menu_config: return

        menu = QMenu(self)
        for entry in self.context_menu_config[menu_type]:
            if entry.get("separator"):
                menu.addSeparator()
            elif entry.get("command"):
                cmd_id = entry["command"]
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
        self.api.input_system.handle_canvas_event(self._create_tool_event(event))
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.api.input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton: self.setDragMode(QGraphicsView.NoDrag)
        self.api.input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseReleaseEvent(event)

    def load_harness(self, harness):
        from ui.items import DeviceItem
        self.scene.clear()
        if not harness: return
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # FIX: Use calculated grid spacing (float) instead of int(25)
        transformer = self.api.transformer
        grid_spacing = transformer.mm_to_px(transformer.grid_size_mm)
        
        if grid_spacing < 2.0: grid_spacing = 25.0

        grid_pen = QPen(QColor(THEME_FALLBACK["grid_color"]))
        grid_pen.setWidth(0)
        painter.setPen(grid_pen)
        
        # Calculate start points (Anchored to 0,0)
        left = math.floor(rect.left() / grid_spacing) * grid_spacing
        top = math.floor(rect.top() / grid_spacing) * grid_spacing
        
        lines = []
        x = left
        while x < rect.right():
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
            x += grid_spacing
            
        y = top
        while y < rect.bottom():
             lines.append(QLineF(rect.left(), y, rect.right(), y))
             y += grid_spacing
             
        painter.drawLines(lines)