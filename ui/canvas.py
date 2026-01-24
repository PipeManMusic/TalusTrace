"""
Canvas and scene management for Talus Trace UI.

Provides QGraphicsView-based canvas, event dispatch, and model synchronization.
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QMouseEvent
from api.manager import APIManager

class CanvasEvent:
    """Wraps a Qt event with scene position and item context for canvas interactions."""
    def __init__(self, original_event, scene_pos, scene_item=None, item_at=None, type=None):
        """Initialize a CanvasEvent with event, scene position, and optional item context."""
        self.original_event = original_event
        self.scene_pos = scene_pos
        self.scene_item = scene_item
        self.item_at = item_at
        self.type = type
        # Add mime_data for drag/drop events
        if hasattr(original_event, 'mimeData') and callable(getattr(original_event, 'mimeData', None)):
            self.mime_data = original_event.mimeData()
        else:
            self.mime_data = None
        # Add button attribute if present in original_event
        if hasattr(original_event, 'button'):
            self.button = original_event.button()

class HarnessCanvas(QGraphicsView):
    """QGraphicsView subclass for the main harness canvas, handling model sync and UI events."""
    def keyPressEvent(self, event):
        """Handle key press events, including delete for selected items."""
        from api.manager import APIManager
        api = APIManager.get_instance()
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                model = getattr(item, 'model', None)
                if model is not None and hasattr(api.context.harness, 'devices') and model in api.context.harness.devices:
                    api.context.harness.devices.remove(model)
                    api.dispatch("model_changed", {"action": "remove", "item": model})
            event.accept()
        else:
            super().keyPressEvent(event)

    def on_model_changed(self, data):
        """Respond to model changes by updating or removing scene items as needed."""
        print(f"[DEBUG] HarnessCanvas.on_model_changed called with: {data}")
        # Robustly handle all device actions: add, update, move, remove, delete
        if not data or 'action' not in data or 'item' not in data:
            print("[DEBUG] model_changed: missing action or item")
            return
        action = data['action']
        device = data['item']
        api = APIManager.get_instance()
        # Always use device_id for registry lookup, not object identity
        device_id = getattr(device, 'id', None)
        item = api.get_scene_item(device_id)

        if action in ('remove', 'delete'):
            print(f"[DEBUG] Attempting to remove item for device_id={device_id}, item={item}")
            removed = False
            if item is not None:
                if hasattr(item, 'setSelected'):
                    item.setSelected(False)
                self.scene.removeItem(item)
                api.unregister_scene_item(device_id)
                removed = True
                print(f"[DEBUG] Removed item for device_id={device_id}")
            else:
                # Defensive: try to find and remove any DeviceItem with matching id
                for scene_item in list(self.scene.items()):
                    if hasattr(scene_item, 'model') and getattr(scene_item.model, 'id', None) == device_id:
                        if hasattr(scene_item, 'setSelected'):
                            scene_item.setSelected(False)
                        self.scene.removeItem(scene_item)
                        api.unregister_scene_item(device_id)
                        removed = True
                        print(f"[DEBUG] Fallback removed item for device_id={device_id}")
                        break
                else:
                    print(f"[DEBUG] No item found for device_id={device_id}")
            # If the removed item was selected, clear selection in the scene
            if removed and hasattr(self.scene, 'clearSelection'):
                self.scene.clearSelection()
        elif action in ('add',):
            from core.device import Device, Pin
            if isinstance(device, Pin):
                # Find parent device and its DeviceItem
                parent_id = getattr(device, 'device_id', None)
                parent_item = api.get_scene_item(parent_id)
                if parent_item is not None:
                    from ui.items.pin import PinItem
                    pin_item = PinItem(device, parent_item)
                    pin_item.setPos(device.x, device.y)
                    print(f"[DEBUG] Added PinItem for pin_id={device_id} to DeviceItem {parent_id}")
                else:
                    print(f"[DEBUG] Could not find DeviceItem for parent device_id={parent_id}")
            else:
                if item is None:
                    from ui.items.device import DeviceItem
                    item = DeviceItem(device)
                    self.scene.addItem(item)
                    api.register_scene_item(device_id, item)
                    print(f"[DEBUG] Added DeviceItem for device_id={device_id}")
        elif action in ('update', 'move'):
            if item is not None:
                item.model = device
                if hasattr(item, 'update_from_model'):
                    item.update_from_model()

    def contextMenuEvent(self, event):
        """Show the context menu for the canvas if available."""
        api = APIManager.get_instance()
        if hasattr(api, 'open_context_menu'):
            api.open_context_menu(event)
        event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Dispatch double-click events to the tool system and base handler."""
        self._dispatch(event)
        super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        """Handle drag enter events and dispatch to the tool system."""
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drag_enter'):
            api.handle_drag_enter(event)
        self._dispatch(event, event_type="DRAG_ENTER")
        event.accept()

    def dropEvent(self, event):
        """Handle drop events and dispatch to the tool system."""
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drop'):
            api.handle_drop(event)
        self._dispatch(event, event_type="DROP")
        event.accept()

    def wheelEvent(self, event):
        """Zoom in/out on wheel events, or pass to base handler."""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        angle_delta = event.angleDelta().y()
        if angle_delta > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        elif angle_delta < 0:
            self.scale(zoom_out_factor, zoom_out_factor)
        else:
            super().wheelEvent(event)

    def __init__(self, parent=None):
        """Initialize the canvas, scene, theme, and event subscriptions."""
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Theme
        try:
            from ui.coordinates import THEME_FALLBACK
            self._theme = THEME_FALLBACK
        except Exception:
            self._theme = {"canvas_bg": "#2E2E2E", "grid_color": "#444444"}

        # Navigation
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Visuals
        from PySide6.QtGui import QColor
        self.setBackgroundBrush(QColor(self._theme.get("canvas_bg", "#2E2E2E")))

        # Subscribe to model_changed for device deletion
        api = APIManager.get_instance()
        if hasattr(api, 'subscribe'):
            api.subscribe('model_changed', self.on_model_changed)

    def drawBackground(self, painter, rect):
        """Draw the background grid and call the base background renderer."""
        super().drawBackground(painter, rect)
        # Draw grid
        color = self._theme.get("grid_color", "#444444")
        from PySide6.QtGui import QColor
        grid_pen = QColor(color)
        painter.setPen(grid_pen)
        grid_size = 5.0
        left = int(rect.left()) - (int(rect.left()) % int(grid_size))
        top = int(rect.top()) - (int(rect.top()) % int(grid_size))
        right = int(rect.right())
        bottom = int(rect.bottom())
        x = left
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size
        y = top
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size

    def load_harness(self, harness):
        """Populate the scene with items from the harness model (devices and wires)."""
        self.scene.clear()
        api = APIManager.get_instance()
        # Devices
        from ui.items.device import DeviceItem
        for dev in getattr(harness, 'devices', []):
            item = DeviceItem(dev)
            self.scene.addItem(item)
            api.register_scene_item(dev.id, item)
        # Wires
        from ui.items.wire import WireItem
        for wire in getattr(harness, 'wires', []):
            item = WireItem(wire)
            self.scene.addItem(item)
            api.register_scene_item(wire.id, item)

    def zoom_extents(self):
        """Zoom the view to fit all items in the scene with padding."""
        rect = self.scene.itemsBoundingRect()
        if rect.isNull(): return
        pad = max(rect.width(), rect.height()) * 0.1
        rect.adjust(-pad, -pad, pad, pad)
        self.fitInView(rect, Qt.KeepAspectRatio)

    # --- Tool Event Dispatching ---
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events, including tool dispatch and drag mode switching."""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            super().mousePressEvent(event)
            return
        self._dispatch(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events and dispatch to the tool system."""
        self._dispatch(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release events, including tool dispatch and drag mode switching."""
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            super().mouseReleaseEvent(event)
            return
        self._dispatch(event)
        super().mouseReleaseEvent(event)

    def _dispatch(self, qt_event, event_type=None):
        """Forward a Qt event to the InputSystem, wrapping with scene/item context."""
        api = APIManager.get_instance()
        if not api.input_system:
            return
        pos = qt_event.position()
        from PySide6.QtCore import QPointF, QPoint
        if isinstance(pos, QPointF):
            scene_pos = self.mapToScene(pos.toPoint())
        elif isinstance(pos, QPoint):
            scene_pos = self.mapToScene(pos)
        else:
            scene_pos = self.mapToScene(0, 0)
        item = self.scene.itemAt(scene_pos, self.transform())
        evt = CanvasEvent(qt_event, scene_pos, scene_item=item, item_at=item, type=event_type)
        if hasattr(qt_event, 'button'):
            evt.button = qt_event.button()
        # Route all events, including right-clicks, through InputSystem
        api.input_system.handle_canvas_event(evt)