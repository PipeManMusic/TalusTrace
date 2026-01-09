from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QMouseEvent
from PySide6.QtCore import Qt, QLineF, QRectF
from ui.coordinates import THEME_FALLBACK
from ui.items import DeviceItem
from api.manager import APIManager
from core.device import Device, Pin

class CanvasEvent:
    def __init__(self, view_event, scene_pos, scene, scene_item=None):
        self.original_event = view_event
        self.pos_mm = scene_pos
        self.scene = scene
        self.scene_item = scene_item


class HarnessCanvas(QGraphicsView):

    GRID_SIZE_MM = 25.0

    def zoom_extents(self):
        """Fits all items in the scene into view (stub for test)."""
        self.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def show_context_menu(self, pos):
        from ui.layout_manager import LayoutManager
        from ui.items import DeviceItem
        menu_manager = LayoutManager().get_context_menu_manager()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        item_type = None
        if item is not None:
            # Determine type for context menu
            from ui.items import DeviceItem
            if isinstance(item, DeviceItem):
                item_type = 'device'
            # Add more types as needed (e.g., WireItem)
            elif hasattr(item, 'wire') or hasattr(item, 'is_wire'):
                item_type = 'wire'
        if not item_type:
            return
        menu = menu_manager.build_menu(item_type, parent=self)
        if menu:
            menu.exec(self.mapToGlobal(pos))

    def contextMenuEvent(self, event):
        # Use event.position().toPoint() for Qt6 compliance
        self.show_context_menu(event.position().toPoint())

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)  # CRITICAL: PH5-CLN.3 Enable hover tracking
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        self.scale(1.0, 1.0)

        # Subscribe to 'view.zoom_to' event
        APIManager.get_instance().subscribe(self._on_zoom_to)

    def _on_zoom_to(self, event):
        # Expects event dict with 'event' and 'target_id'
        if event.get('event') != 'view.zoom_to':
            return
        target_id = event.get('target_id')
        if not target_id:
            return
        # Find the DeviceItem with matching device.id
        for item in self.scene.items():
            # DeviceItem is imported at top
            if isinstance(item, DeviceItem) and hasattr(item, 'device') and getattr(item.device, 'id', None) == target_id:
                self.fitInView(item.sceneBoundingRect(), Qt.KeepAspectRatio)
                # Optionally select the item
                item.setSelected(True)
                break

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        factor = 1.15 if zoom_in else 1 / 1.15
        self.scale(factor, factor)
        event.accept()

    def load_harness(self, harness):
        self.scene.clear()
        if not harness: return
        for device in harness.devices:
            item = DeviceItem(device)
            self.scene.addItem(item)

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
        harness = APIManager.get_instance().context.harness
        new_dev = Device(
            id=f"{part_id}_{len(harness.devices)+1}",
            label=part_id.title(),
            x=x, y=y
        )
        new_dev.pins.append(Pin("1", -10, 0))
        new_dev.pins.append(Pin("2", 10, 0))
        harness.devices.append(new_dev)
        
        from ui.items import DeviceItem
        item = DeviceItem(new_dev)
        self.scene.addItem(item)

    def _create_tool_event(self, event: QMouseEvent):
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        return CanvasEvent(event, scene_pos, self.scene, item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            super().mousePressEvent(event)
            return

        if event.button() == Qt.RightButton:
            # Use event.position().toPoint() for Qt6 compliance
            self.show_context_menu(event.position().toPoint())
            return

        tool = APIManager.get_instance().tool_manager.active_tool
        if tool:
            tool.on_mouse_press(self._create_tool_event(event))
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        print(">> DEBUG: Double Click Detected in Canvas") # <--- DEBUG
        tool = APIManager.get_instance().tool_manager.active_tool
        if tool:
            tool.on_mouse_double_click(self._create_tool_event(event))
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        # PH5-CLN.3: Smart Cursor Affordance with Debug Logging
        from ui.items import PinItem, DeviceItem
        # Use event.position().toPoint() for Qt6 compliance (avoids deprecation warning)
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        # Increase search rect to 8x8mm for robust hit detection
        search_rect = QRectF(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8)
        items = self.scene.items(search_rect, Qt.IntersectsItemShape, Qt.DescendingOrder, self.transform())
        print(f"\n[DEBUG] Mouse Move at Scene Pos: {scene_pos.x():.2f}, {scene_pos.y():.2f} (viewport: {pos.x()}, {pos.y()})")
        print(f"[DEBUG] Search rect: {search_rect}")
        print(f"[DEBUG] Items found: {len(items)}")
        for i, item in enumerate(items):
            print(f"  {i}: Type={type(item).__name__}, Visible={item.isVisible()}, Z={item.zValue()}")
            if isinstance(item, DeviceItem):
                print(f"    [DEBUG] DeviceItem.device.id: {getattr(item.device, 'id', None)}")
                print(f"    [DEBUG] DeviceItem.sceneBoundingRect: {item.sceneBoundingRect()}")
        # Fallback: try itemAt for precise hit
        if not items:
            item_at = self.scene.itemAt(scene_pos, self.transform())
            print(f"[DEBUG] Fallback itemAt: {item_at} at {scene_pos}")
            if item_at:
                items = [item_at]
        # Print all DeviceItems in scene for debug
        for item in self.scene.items():
            if isinstance(item, DeviceItem):
                print(f"[DEBUG] Scene DeviceItem: id={getattr(item.device, 'id', None)}, sceneBoundingRect={item.sceneBoundingRect()}")
        new_cursor = Qt.ArrowCursor
        for item in items:
            if isinstance(item, PinItem):
                new_cursor = Qt.CrossCursor
                break
            elif isinstance(item, DeviceItem):
                new_cursor = Qt.OpenHandCursor
                break
        print(f"[DEBUG] Cursor set to: {new_cursor}")
        self.viewport().setCursor(new_cursor)

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