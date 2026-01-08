from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent
from PySide6.QtCore import Qt, QLineF
from ui.coordinates import THEME_FALLBACK
from ui.items import DeviceItem
from api.manager import APIManager
from core.device import Device, Pin

class CanvasEvent:
    """Standardized event package for tools."""
    def __init__(self, view_event, scene_pos, scene_item=None):
        self.original_event = view_event
        self.pos_mm = scene_pos
        self.scene_item = scene_item

class HarnessCanvas(QGraphicsView):
    GRID_SIZE_MM = 25.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setAcceptDrops(True) # Enable Drag & Drop
        self.setDragMode(QGraphicsView.NoDrag) 
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        self.scale(1.0, 1.0)

    def load_harness(self, harness):
        self.scene.clear()
        if not harness: return
        for device in harness.devices:
            item = DeviceItem(device)
            self.scene.addItem(item)

    # --- Drag & Drop Interface ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        part_id = event.mimeData().text()
        pos = self.mapToScene(event.pos())
        
        print(f">> Dropped Part: {part_id} at ({pos.x():.1f}, {pos.y():.1f})")
        self._instantiate_part(part_id, pos.x(), pos.y())
        event.acceptProposedAction()

    def _instantiate_part(self, part_id, x, y):
        from api.manager import APIManager
        harness = APIManager.get_instance().context.harness
        
        # Create Device
        new_dev = Device(
            id=f"{part_id}_{len(harness.devices)+1}",
            label=part_id.title(),
            x=x, 
            y=y
        )
        
        # Add default pins (Prototype logic)
        new_dev.pins.append(Pin("1", -10, 0))
        new_dev.pins.append(Pin("2", 10, 0))
        
        # Add to Model
        harness.devices.append(new_dev)
        
        # Add to Scene
        from ui.items import DeviceItem
        item = DeviceItem(new_dev)
        self.scene.addItem(item)

    # --- Event Routing ---
    def _create_tool_event(self, event: QMouseEvent):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        return CanvasEvent(event, scene_pos, item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            super().mousePressEvent(event)
            return

        tool = APIManager.get_instance().tool_manager.active_tool
        if tool:
            tool.on_mouse_press(self._create_tool_event(event))
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        tool = APIManager.get_instance().tool_manager.active_tool
        if tool:
            tool.on_mouse_move(self._create_tool_event(event))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            super().mouseReleaseEvent(event)
            return

        tool = APIManager.get_instance().tool_manager.active_tool
        if tool:
            tool.on_mouse_release(self._create_tool_event(event))
        super().mouseReleaseEvent(event)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        grid_pen = QPen(QColor(THEME_FALLBACK["grid_color"]))
        grid_pen.setWidth(0)
        painter.setPen(grid_pen)
        
        left = int(rect.left()) - (int(rect.left()) % int(self.GRID_SIZE_MM))
        top = int(rect.top()) - (int(rect.top()) % int(self.GRID_SIZE_MM))
        
        lines = []
        for x in range(left, int(rect.right()), int(self.GRID_SIZE_MM)):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), int(self.GRID_SIZE_MM)):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        painter.drawLines(lines)