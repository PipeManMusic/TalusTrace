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
    GRID_SIZE_MM = 25.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        
        # Viewport Configuration
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.setDragMode(QGraphicsView.NoDrag)
        
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        self.scale(1.0, 1.0)

    def _create_tool_event(self, event: QMouseEvent):
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        return CanvasEvent(event, scene_pos, self.scene, item)

    def wheelEvent(self, event):
        """Standard Zooming Logic."""
        zoom_in = event.angleDelta().y() > 0
        factor = 1.15 if zoom_in else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def mousePressEvent(self, event):
        """Handles Panning (Middle) and Tool Dispatching (Left/Right)."""
        # 1. Pan with Middle Button
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake_event)
            return

        # 2. Context Menu
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.position().toPoint())
            return

        # 3. Dispatch to Active Tool (Placement, Select, etc.)
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        
        # 4. Allow Native Dragging if tool permits (e.g., SelectTool)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Updates cursor, tools, and native drag items."""
        event_obj = self._create_tool_event(event)
        
        # Dispatch to Tool
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        
        # Update Native Dragging
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Ends Panning and Tool actions."""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        event_obj = self._create_tool_event(event)
        APIManager.get_instance().input_system.handle_canvas_event(event_obj)
        super().mouseDoubleClickEvent(event)

    def load_harness(self, harness):
        """Rebuilds the scene from the Harness Model."""
        from ui.items import DeviceItem, BundleItem
        self.scene.clear()
        if not harness: return
        
        # 1. Add Devices
        device_map = {d.id: d for d in harness.devices}
        for device in harness.devices:
            self.scene.addItem(DeviceItem(device))
            
        # 2. Add Wires
        for wire in getattr(harness, 'wires', []):
            d_from = device_map.get(getattr(wire, 'from_conn', None))
            d_to = device_map.get(getattr(wire, 'to_conn', None))
            
            # Simple pin offset logic (can be expanded)
            from_pt = (d_from.x, d_from.y) if d_from else (0, 0)
            to_pt = (d_to.x, d_to.y) if d_to else (0, 0)
            
            path_nodes = [from_pt] + list(getattr(wire, 'points', [])) + [to_pt]
            wire_diameters = [getattr(wire, 'diameter_mm', 1.0)] * len(path_nodes)
            self.scene.addItem(BundleItem(path_nodes, wire_diameters, wire_model=wire))

    def drawBackground(self, painter, rect):
        """Renders the grid."""
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

    def show_context_menu(self, pos):
        from ui.layout_manager import LayoutManager
        from ui.items import DeviceItem
        menu_manager = LayoutManager().get_context_menu_manager()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        
        item_type = None
        if isinstance(item, DeviceItem):
            item_type = 'device'
        elif hasattr(item, 'wire'):
            item_type = 'wire'
            
        if item_type:
            menu = menu_manager.build_menu(item_type, parent=self)
            if menu:
                menu.exec(self.mapToGlobal(pos))