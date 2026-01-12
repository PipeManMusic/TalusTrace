import math
import os
import yaml
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu, QGraphicsItem
from PySide6.QtGui import QPainter, QBrush, QPen, QMouseEvent, QAction
from PySide6.QtCore import Qt, QLineF
from api.manager import APIManager
from api.actions import registry
from ui.theme import ThemeManager

# Fix: Import specific item classes
from ui.items.device import DeviceItem
from ui.items.wire import WireItem, TwistedPairItem

class CanvasEvent:
    def __init__(self, view_event, scene_pos, scene):
        self.original_event = view_event
        self.scene_pos = scene_pos 
        self.pos_mm = scene_pos 
        self.scene = scene
        self.scene_item = scene.itemAt(scene_pos, QGraphicsView().transform())

class HarnessCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.theme = ThemeManager() 
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Initial Setup
        self._update_view_scale()
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        self._apply_theme()
        
        self.context_menu_config = self._load_context_menu_config()
        
        # Subscriptions
        self.api.subscribe("model_changed", self.refresh)
        self.api.subscribe("theme_changed", self._on_theme_changed)
        self.api.subscribe("settings_changed", self._on_settings_changed)

    def _load_context_menu_config(self):
        """Loads context menu structure from YAML config."""
        path = os.path.join("resources", "config", "ui_layout.yaml")
        if not os.path.exists(path): return {}
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return data.get("context_menu", {})
        except Exception:
            return {}

    def _update_view_scale(self):
        dpi = getattr(self.api.settings, 'pixels_per_inch', 96.0)
        self.pixels_per_mm = dpi / 25.4
        self.resetTransform()
        self.scale(self.pixels_per_mm, self.pixels_per_mm)

    def _apply_theme(self):
        self.theme = ThemeManager() 
        bg_color = self.theme.get_color("canvas_bg")
        self.setBackgroundBrush(QBrush(bg_color))

    def _on_theme_changed(self, data):
        self._apply_theme()
        self.scene.update()

    def _on_settings_changed(self, data):
        self._update_view_scale()
        self.scene.update()

    def refresh(self, data):
        self.load_harness(self.api.context.harness)

    def load_harness(self, harness):
        """Rebuilds the scene from the Harness Model."""
        self.scene.clear()
        if not harness: return
        
        # 1. Devices
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))
            
        # 2. Wires (Factory Logic)
        for wire in harness.wires:
            if not (wire.from_conn and wire.to_conn): continue
            
            item = None
            # CHECK WIRE TYPE
            if getattr(wire, 'type', 'STANDARD') == 'TWISTED_PAIR':
                item = TwistedPairItem(wire.path_nodes, gauge_mm=getattr(wire, 'diameter_mm', 1.0))
            else:
                item = WireItem(wire)
            
            if item:
                self.scene.addItem(item)

    # ... (Rest of event handlers remain standard) ...
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu_type = None
        if item:
            if hasattr(item, 'pin'): menu_type = 'pin'
            elif hasattr(item, 'model'): menu_type = type(item.model).__name__.lower()
        
        if not menu_type or menu_type not in self.context_menu_config: return

        menu = QMenu(self)
        for entry in self.context_menu_config[menu_type]:
            if entry.get("separator"): menu.addSeparator()
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
        return CanvasEvent(event, scene_pos, self.scene)

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

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_mm = 5.0
        if hasattr(self.api, 'settings'): grid_mm = self.api.settings.grid_size_mm
        if grid_mm <= 0: grid_mm = 5.0
        
        color = self.theme.get_color("grid_color")
        grid_pen = QPen(color); grid_pen.setWidth(0)
        painter.setPen(grid_pen)
        
        left = math.floor(rect.left() / grid_mm) * grid_mm
        top = math.floor(rect.top() / grid_mm) * grid_mm
        
        lines = []
        x = left
        while x < rect.right():
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
            x += grid_mm
        y = top
        while y < rect.bottom():
             lines.append(QLineF(rect.left(), y, rect.right(), y))
             y += grid_mm
        painter.drawLines(lines)
    
    def zoom_extents(self):
        rect = self.scene.itemsBoundingRect()
        if not rect.isEmpty(): self.fitInView(rect, Qt.KeepAspectRatio)