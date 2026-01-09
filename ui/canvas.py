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
    def set_active_tool(self, tool):
        self.active_tool = tool

    def mouseMoveEvent(self, event):
        if hasattr(self, 'active_tool') and self.active_tool:
            scene_pos = self.mapToScene(event.position().toPoint() if hasattr(event, 'position') else event.pos())
            self.active_tool.on_mouse_move(scene_pos)
        else:
            super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if hasattr(self, 'active_tool') and self.active_tool:
            scene_pos = self.mapToScene(event.position().toPoint() if hasattr(event, 'position') else event.pos())
            self.active_tool.on_mouse_press(scene_pos)
        else:
            super().mousePressEvent(event)

    def _init_move_tool(self):
        from tools.move_tool import MoveTool
        self._move_tool = MoveTool()
        self._dragging_device = None
        self._last_mouse_pos = None

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
        # Use event.pos() for QContextMenuEvent compatibility
        self.show_context_menu(event.pos())

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self.setBackgroundBrush(QBrush(QColor(THEME_FALLBACK["canvas_bg"])))
        self.scale(1.0, 1.0)

        # MoveTool integration
        self._init_move_tool()

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
        if not harness:
            return
        # 1. Add devices
        device_map = {d.id: d for d in harness.devices}
        for device in harness.devices:
            item = DeviceItem(device)
            self.scene.addItem(item)
        # 2. Add wires (BundleItem)
        from ui.items import BundleItem
        for wire in getattr(harness, 'wires', []):
            d_from = device_map.get(getattr(wire, 'from_conn', None))
            d_to = device_map.get(getattr(wire, 'to_conn', None))
            def find_pin(device, pin_id):
                if device and hasattr(device, 'pins'):
                    for pin in device.pins:
                        if pin.id == pin_id:
                            return pin
                return None
            pin_from = find_pin(d_from, getattr(wire, 'from_pin', ''))
            pin_to = find_pin(d_to, getattr(wire, 'to_pin', ''))
            from_pt = (d_from.x + (pin_from.x if pin_from else 0), d_from.y + (pin_from.y if pin_from else 0)) if d_from else (0, 0)
            to_pt = (d_to.x + (pin_to.x if pin_to else 0), d_to.y + (pin_to.y if pin_to else 0)) if d_to else (0, 0)
            path_nodes = [from_pt] + list(getattr(wire, 'points', [])) + [to_pt]
            wire_diameters = [getattr(wire, 'diameter_mm', 1.0)] * len(path_nodes)
            bundle_item = BundleItem(path_nodes, wire_diameters, wire_model=wire)
            self.scene.addItem(bundle_item)

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
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        # Always pass scene=self.scene to ToolEvent
        return CanvasEvent(event, scene_pos, self.scene, item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            super().mousePressEvent(event)
            return

        if event.button() == Qt.RightButton:
            self.show_context_menu(event.position().toPoint())
            return

        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())
        from ui.items import DeviceItem
        # Shift+LeftClick places a generic device
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ShiftModifier:
            from api.actions import registry
            registry.execute("tool.add_generic_device", pos=(scene_pos.x(), scene_pos.y()))
            return
        if event.button() == Qt.LeftButton and isinstance(item, DeviceItem):
            self._dragging_device = item
            self._last_mouse_pos = scene_pos
            self._move_tool.start(item.device, item)
            return

        # Central event dispatch
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))

    def mouseDoubleClickEvent(self, event):
        print(">> DEBUG: Double Click Detected in Canvas") # <--- DEBUG
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        from ui.items import PinItem, DeviceItem
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        # If dragging a device, use MoveTool
        if self._dragging_device is not None and self._last_mouse_pos is not None:
            dx = scene_pos.x() - self._last_mouse_pos.x()
            dy = scene_pos.y() - self._last_mouse_pos.y()
            self._move_tool.update(dx, dy)
            self._last_mouse_pos = scene_pos
            return

        # PH5-CLN.3: Smart Cursor Affordance
        search_rect = QRectF(scene_pos.x() - 4, scene_pos.y() - 4, 8, 8)
        items = self.scene.items(search_rect, Qt.IntersectsItemShape, Qt.DescendingOrder, self.transform())
        if not items:
            item_at = self.scene.itemAt(scene_pos, self.transform())
            if item_at:
                items = [item_at]
        new_cursor = Qt.ArrowCursor
        for item in items:
            if isinstance(item, PinItem):
                new_cursor = Qt.CrossCursor
                break
            elif isinstance(item, DeviceItem):
                new_cursor = Qt.OpenHandCursor
                break
        self.viewport().setCursor(new_cursor)

        # Central event dispatch
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        # Complete MoveTool drag if active
        if self._dragging_device is not None:
            self._move_tool.commit()
            self._dragging_device = None
            self._last_mouse_pos = None
            return

        # Handle middle mouse button drag mode
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.NoDrag)
            super().mouseReleaseEvent(event)
            return

        # Central event dispatch
        APIManager.get_instance().input_system.handle_canvas_event(self._create_tool_event(event))
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