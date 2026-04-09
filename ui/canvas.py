"""
Pure rendering canvas for Talus Trace UI.

This canvas is a QGraphicsView subclass responsible ONLY for rendering the current model state.
It does not handle any input, selection, tool, or dispatcher logic. All such logic is managed by
dedicated managers (InputSystem, Dispatcher, SelectionManager, etc.).

Responsibilities:
  - Render devices, pins, wires, and other items from the model.
  - Update/redraw when notified of model changes.
  - Expose simple update/redraw methods (e.g., load_harness, zoom_extents).
  - Draw background grid.

All event handling, selection, and command logic must be routed through the appropriate manager.
The canvas is a pure view.
"""
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from api.manager import APIManager

class HarnessCanvas(QGraphicsView):
    """Canvas view for displaying and interacting with harness items on the scene."""
    def dragEnterEvent(self, event):
        """Forward drag enter events to APIManager for contract compliance."""
        api = APIManager.get_instance()
        # Delegate acceptance decision to API - View does not parse mime formats
        if hasattr(api, 'handle_drag_enter'):
            accepted = api.handle_drag_enter(event)
            if accepted:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        """Forward drop events to APIManager for contract compliance."""
        api = APIManager.get_instance()
        if hasattr(api, 'handle_drop'):
            api.handle_drop(event)
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        """Route Delete key to dispatcher for device/pin removal in headless tests."""
        if event.key() == Qt.Key_Delete:
            from api.actions import registry
            from core.device import Device
            from core.pin import Pin
            api = APIManager.get_instance()
            ctx = api.context
            
            # Set pin/device on context for delete handler
            selection_manager = getattr(ctx, 'selection_manager', None)
            if selection_manager and getattr(selection_manager, 'selected_models', None):
                selected_list = selection_manager.selected_models
                if selected_list:
                    selected = selected_list[0]
                    if isinstance(selected, Pin):
                        ctx.pin = selected
                        # Also find and set parent device
                        for dev in ctx.harness.devices:
                            if hasattr(dev, 'pins') and any(p.id == selected.id for p in dev.pins):
                                ctx.device = dev
                                break
                    elif isinstance(selected, Device):
                        ctx.device = selected
                        ctx.pin = None
            
            registry.execute("edit.delete", ctx)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        """Zoom in/out on wheel scroll (contract compliance)."""
        # Standard zoom logic: scale view on wheel
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
        event.accept()

    def contextMenuEvent(self, event):
        """Forward context menu events to APIManager for contract compliance."""
        api = APIManager.get_instance()
        if hasattr(api, 'open_context_menu'):
            # Detect item at the context menu event position
            item = None
            try:
                from PySide6.QtGui import QTransform
                scene_pos = self.mapToScene(event.pos())
                import sys
                print(f"[DEBUG][canvas.contextMenuEvent] event.pos()={event.pos()}, scene_pos={scene_pos}", file=sys.stderr)
                if self.scene:
                    item = self.scene.itemAt(scene_pos, QTransform())
                    print(f"[DEBUG][canvas.contextMenuEvent] item={item}, type={type(item) if item else None}, has model={hasattr(item, 'model') if item else None}", file=sys.stderr)
            except Exception as e:
                import traceback
                traceback.print_exc()
            api.open_context_menu(event, item=item)
        else:
            super().contextMenuEvent(event)
    """
    Pure rendering canvas for Talus Trace. Only responsible for drawing the scene.
    All input, selection, and tool logic is handled elsewhere.
    """
    def __init__(self, parent=None):
        """Initialize the canvas with empty scene and configure rendering."""
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

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
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        # Visuals
        from PySide6.QtGui import QColor
        self.setBackgroundBrush(QColor(self._theme.get("canvas_bg", "#2E2E2E")))

        # Subscribe to model_changed for device deletion
        api = APIManager.get_instance()
        # Subscribe to all API events for robust model sync
        if hasattr(api, 'subscribe_to_all'):
            api.subscribe_to_all(self._on_any_event)

    def _on_any_event(self, event_type, data):
        """Handle any API event that could affect the canvas rendering."""
        # Only reload for undo/redo, not for every event
        if not hasattr(self, '_is_reloading'):
            self._is_reloading = False
        if self._is_reloading:
            return
        if event_type in ("undo", "redo"):
            try:
                self._is_reloading = True
                api = APIManager.get_instance()
                harness = getattr(api.context, 'harness', None)
                if harness is not None:
                    self.load_harness(harness)
            finally:
                self._is_reloading = False
        elif event_type == "model_changed":
            self.on_model_changed(data)

    def on_model_changed(self, data):
        """Respond to model changes by updating or removing scene items as needed."""
        # Only update the scene visually, never mutate model or selection.
        from api.manager import APIManager
        api = APIManager.get_instance()
        action = data.get("action") if isinstance(data, dict) else None
        item = data.get("item") if isinstance(data, dict) else None
        # Remove scene item when model is deleted
        if action == "remove" and item is not None:
            model_id = getattr(item, "id", None)
            scene_item = api.get_scene_item(model_id)
            if scene_item is not None:
                if hasattr(scene_item, "setSelected"):
                    scene_item.setSelected(False)
                self.scene.removeItem(scene_item)
                api.unregister_scene_item(model_id)
        # Add or update scene items for model additions
        elif action == "add" and item is not None:
            model_id = getattr(item, "id", None)
            if model_id and api.get_scene_item(model_id) is None:
                from core.pin import Pin
                if isinstance(item, Pin):
                    parent_device_item = api.get_scene_item(getattr(item, "device_id", None))
                    if parent_device_item is not None:
                        from ui.items.pin import PinItem
                        pin_item = PinItem(item, parent_device_item)
                        pin_item.setPos(item.x, item.y)
                        # Ensure the pin is added to the scene
                        scene_ref = parent_device_item.scene() or self.scene
                        if scene_ref is not None:
                            scene_ref.addItem(pin_item)
                        api.register_scene_item(model_id, pin_item)
                    return
                from core.wire import Wire
                if isinstance(item, Wire):
                    from ui.items.wire import WireItem
                    wire_item = WireItem(item)
                    self.scene.addItem(wire_item)
                    api.register_scene_item(model_id, wire_item)
                    return
                from ui.items.device import DeviceItem
                device_item = DeviceItem(item)
                self.scene.addItem(device_item)
                api.register_scene_item(model_id, device_item)
                # Register PinItems created by DeviceItem
                if hasattr(item, 'pins'):
                    for pin in item.pins:
                        pin_items = [child for child in device_item.childItems() 
                                   if hasattr(child, 'model') and hasattr(child.model, 'id') 
                                   and child.model.id == pin.id]
                        if pin_items:
                            api.register_scene_item(pin.id, pin_items[0])
        # Update scene items when model properties change (includes position moves)
        elif action in ("update", "move") and item is not None:
            model_id = getattr(item, "id", None)
            scene_item = api.get_scene_item(model_id)
            if scene_item is not None:
                # Update position if the item has x and y coordinates
                if hasattr(item, 'x') and hasattr(item, 'y'):
                    scene_item.setPos(item.x, item.y)
                # Update other properties as needed (angle, label, etc.)
                if hasattr(item, 'rotation') and hasattr(scene_item, 'rotation'):
                    scene_item.setRotation(item.rotation)
            # Update connected wire endpoints when a device or pin moves
            if action == "move":
                api._update_connected_wires(item)
        # For other actions, do nothing (extend as needed)

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
            # Register PinItems created by DeviceItem
            if hasattr(dev, 'pins'):
                for pin in dev.pins:
                    pin_items = [child for child in item.childItems() 
                               if hasattr(child, 'model') and hasattr(child.model, 'id') 
                               and child.model.id == pin.id]
                    if pin_items:
                        api.register_scene_item(pin.id, pin_items[0])
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