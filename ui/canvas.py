import math
import os
import yaml
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent, QAction
from PySide6.QtCore import Qt, QLineF, QPointF
from api.manager import APIManager
from api.actions import registry
from ui.theme import ThemeManager

class CanvasEvent:
    def __init__(self, view_event, scene_pos, scene):
        self.original_event = view_event
        self.scene_pos = scene_pos 
        # In World Space architecture, scene coordinates ARE physical coordinates (mm)
        self.pos_mm = scene_pos 
        self.scene = scene
        self.scene_item = scene.itemAt(scene_pos, QGraphicsView().transform())

class HarnessCanvas(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.theme = ThemeManager() # UI owns the visuals
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # --- ARCHITECTURE FIX: VIEW SCALING ---
        # 1. Get Monitor Calibration from Settings (Physics)
        # Default to 96 DPI if settings not loaded yet
        dpi = getattr(self.api.settings, 'pixels_per_inch', 96.0)
        
        # 2. Calculate Scale: (DPI pixels / 1 inch) * (1 inch / 25.4 mm)
        self.pixels_per_mm = dpi / 25.4
        
        # 3. Scale the View so 1.0 unit in Scene = 1.0 mm on Screen
        self.scale(self.pixels_per_mm, self.pixels_per_mm)
        
        # Standard Setup
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        # Scene is effectively infinite MM
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        # Set Background from Theme
        bg_color = self.theme.get_color("canvas_bg")
        self.setBackgroundBrush(QBrush(bg_color))
        
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
        # mapToScene handles the scaling (Pixels -> MM) automatically
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

    def load_harness(self, harness):
        from ui.items.device import DeviceItem
        from ui.items.wire import WireItem
        
        self.scene.clear()
        if not harness: return
        
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))
            
        for wire in harness.wires:
            if wire.from_conn and wire.to_conn:
                self.scene.addItem(WireItem(wire))

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # 1. Ask API for physics (Grid Size in MM)
        # This is the "Dumb UI" part: it doesn't know 5.0 is the value, it just asks.
        grid_mm = 5.0
        if hasattr(self.api, 'settings'):
            grid_mm = self.api.settings.grid_size_mm
            
        if grid_mm <= 0: grid_mm = 5.0
        
        # 2. Ask Theme for paint (Color)
        color = self.theme.get_color("grid_color")
        grid_pen = QPen(color)
        grid_pen.setWidth(0) # Cosmetic pen (always 1px wide regardless of zoom)
        painter.setPen(grid_pen)
        
        # 3. Draw Grid Lines
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
        if not rect.isEmpty():
            self.fitInView(rect, Qt.KeepAspectRatio)