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
    """
    QGraphicsView subclass for the main harness canvas in Talus Trace.
    Handles event dispatch, model synchronization, and tool event routing for the UI.
    Provides the main interface between the scene, user input, and the model layer.
    """
    def mousePressEvent(self, event):
        """Dispatch mouse press events to the active tool and InputSystem for context menu support. Also handle deselection on blank canvas click."""
        api = APIManager.get_instance()
        scene_pos = self.mapToScene(event.position().toPoint() if hasattr(event, 'position') else event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        canvas_event = CanvasEvent(event, scene_pos, scene_item=item)
        # Route right-clicks through InputSystem for context menu contract
        if hasattr(api, 'input_system') and api.input_system:
            handled = api.input_system.handle_canvas_event(canvas_event)
            if handled:
                super().mousePressEvent(event)
                return
        # Deselect if clicking on blank space (no item under cursor, left click)
        if item is None and event.button() == Qt.LeftButton:
            api.dispatch("selection_changed", {"selection": []})
        # Otherwise, dispatch to tool if present
        tool = getattr(api.tool_manager, 'active_tool', None)
        if tool and hasattr(tool, 'on_mouse_press'):
            tool.on_mouse_press(canvas_event)
        super().mousePressEvent(event)
    def keyPressEvent(self, event):
        """Handle key press events, including delete for selected items, via API contract methods only."""
        api = APIManager.get_instance()
        if event.key() == Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                model = getattr(item, 'model', None)
                if model is not None:
                    # Route all deletions through the dispatcher contract only
                    if hasattr(model, 'pins') and hasattr(model, 'meta'):
                        # Device deletion
                        api.dispatch('edit.delete', {'device': model})
                    elif hasattr(model, 'device_id') and hasattr(model, 'id'):
                        # Pin deletion
                        api.dispatch('edit.delete', {'pin': model})
            event.accept()
        else:
            super().keyPressEvent(event)

    def on_model_changed(self, data):
        """Respond to model changes by updating or removing scene items as needed."""
        from infra.logging import infra_log
        import traceback
        print("\n[DIAG] === on_model_changed CALLED ===")
        print(f"[DIAG] data: {data}")
        traceback.print_stack(limit=6)
        infra_log(f"[CANVAS] on_model_changed called with: {data}", level="debug")
        # Robustly handle all device actions: add, update, move, remove, delete
        if not data or 'action' not in data or 'item' not in data:
            infra_log("[CANVAS] model_changed: missing action or item", level="debug")
            print("[DIAG] model_changed: missing action or item")
            return
        action = data['action']
        model = data['item']
        api = APIManager.get_instance()
        model_id = getattr(model, 'id', None)
        print(f"[DIAG] action={action}, model={model}, type={type(model)}, model_id={model_id}")
        infra_log(f"[CANVAS] on_model_changed: action={action}, model={model}, type={type(model)}, model_id={model_id}", level="debug")
        item = api.get_scene_item(model_id)
        print(f"[DIAG] get_scene_item({model_id}) -> {item}")
        infra_log(f"[CANVAS] on_model_changed: action={action}, model_id={model_id}, item={item}", level="debug")
        # Print all scene items and their model ids
        print("[DIAG] Scene items:")
        for scene_item in list(self.scene.items()):
            mid = getattr(getattr(scene_item, 'model', None), 'id', None)
            print(f"    scene_item={scene_item}, model_id={mid}")
        # Print scene registry state
        if hasattr(api, '_scene_registry'):
            print(f"[DIAG] Scene registry: {list(api._scene_registry.keys())}")

        if action in ('remove', 'delete'):
            from infra.logging import infra_log
            print(f"[DIAG] [REMOVE/DELETE] on_model_changed triggered for action={action}, model_id={model_id}, item={item}")
            infra_log(f"[CANVAS] [REMOVE/DELETE] on_model_changed triggered for action={action}, model_id={model_id}, item={item}", level="debug")
            print(f"[DIAG] [REMOVE/DELETE] Attempting to remove item(s) for model_id={model_id}, item={item}")
            infra_log(f"[CANVAS] [REMOVE/DELETE] Attempting to remove item(s) for model_id={model_id}, item={item}", level="debug")

            def fully_cleanup_item(target_item, target_id):
                print(f"[DIAG] [REMOVE/DELETE] fully_cleanup_item: target_id={target_id}, target_item={target_item}")
                infra_log(f"[CANVAS] [REMOVE/DELETE] fully_cleanup_item: target_id={target_id}, target_item={target_item}", level="debug")
                # Deselect
                if hasattr(target_item, 'setSelected'):
                    target_item.setSelected(False)
                # Disconnect signals if any
                if hasattr(target_item, 'disconnect'):
                    try:
                        target_item.disconnect()
                    except Exception:
                        pass
                # Remove from scene
                self.scene.removeItem(target_item)
                print(f"[DIAG] [REMOVE/DELETE] Removed from scene: {target_item}")
                infra_log(f"[CANVAS] [REMOVE/DELETE] Removed from scene: {target_item}", level="debug")
                # Remove from selection if present
                if hasattr(self.scene, 'selectedItems'):
                    try:
                        selected = self.scene.selectedItems()
                        if target_item in selected:
                            self.scene.clearSelection()
                            print(f"[DIAG] [REMOVE/DELETE] Cleared selection for: {target_item}")
                            infra_log(f"[CANVAS] [REMOVE/DELETE] Cleared selection for: {target_item}", level="debug")
                    except Exception:
                        pass
                # Remove from API registry
                api.unregister_scene_item(target_id)
                print(f"[DIAG] [REMOVE/DELETE] Unregistered from scene registry: {target_id}")
                infra_log(f"[CANVAS] [REMOVE/DELETE] Unregistered from scene registry: {target_id}", level="debug")
                # Print registry state after removal
                if hasattr(api, '_scene_registry'):
                    print(f"[DIAG] [REMOVE/DELETE] Scene registry after removal: {list(api._scene_registry.keys())}")
                    infra_log(f"[CANVAS] [REMOVE/DELETE] Scene registry after removal: {list(api._scene_registry.keys())}", level="debug")

            removed = False
            # Remove the item found by registry lookup (if any)
            if item is not None:
                fully_cleanup_item(item, model_id)
                removed = True
                print(f"[DEBUG] Removed item for model_id={model_id}")
                infra_log(f"[CANVAS] [REMOVE/DELETE] Removed item for model_id={model_id}", level="debug")
            # Defensive: try to find and remove any scene item with matching id (in case registry is stale)
            for scene_item in list(self.scene.items()):
                if hasattr(scene_item, 'model') and getattr(scene_item.model, 'id', None) == model_id:
                    fully_cleanup_item(scene_item, model_id)
                    removed = True
            # --- Robust PinItem removal: if a pin is being removed, always remove all PinItems with matching model id ---
            if hasattr(model, 'device_id') and hasattr(model, 'id'):
                # This is likely a Pin model; remove all PinItems with matching pin id
                for scene_item in list(self.scene.items()):
                    if type(scene_item).__name__ == 'PinItem' and hasattr(scene_item, 'model'):
                        pin_model = getattr(scene_item, 'model', None)
                        if getattr(pin_model, 'id', None) == model_id:
                            fully_cleanup_item(scene_item, model_id)
                            removed = True
                # --- Do NOT mutate parent_device.pins in UI layer. All model mutations must be performed via commands/dispatcher. ---
                # Static enforcement: direct model mutation is forbidden in UI. This block intentionally left blank.
            # If the removed item was selected, clear selection in the scene
            if removed and hasattr(self.scene, 'clearSelection'):
                self.scene.clearSelection()
                print(f"[DIAG] [REMOVE/DELETE] Cleared selection after removal.")
                infra_log(f"[CANVAS] [REMOVE/DELETE] Cleared selection after removal.", level="debug")
        elif action in ('add',):
            from core.device import Device, Pin
            infra_log(f"[CANVAS] on_model_changed: entering 'add' branch, model={model}", level="debug")
            print(f"[DIAG] [ADD] on_model_changed: action=add, model={model}, type={type(model)}, model_id={model_id}")
            if isinstance(model, Pin):
                # Find parent device and its DeviceItem
                parent_id = getattr(model, 'device_id', None)
                parent_item = api.get_scene_item(parent_id)
                print(f"[DIAG] [ADD] Pin add: parent_id={parent_id}, parent_item={parent_item}")
                if parent_item is not None:
                    from ui.items.pin import PinItem
                    pin_item = PinItem(model, parent_item)
                    pin_item.setPos(model.x, model.y)
                    print(f"[DIAG] [ADD] Adding PinItem to scene: pin_id={model_id}, pin_item={pin_item}")
                    self.scene.addItem(pin_item)
                    api.register_scene_item(model_id, pin_item)
                    print(f"[DIAG] [ADD] Registered PinItem in scene registry: pin_id={model_id}")
                    infra_log(f"[CANVAS] Added PinItem for pin_id={model_id} to DeviceItem {parent_id} and registered in scene registry", level="debug")
                else:
                    print(f"[DIAG] [ADD] Could not find DeviceItem for parent device_id={parent_id}")
                    infra_log(f"[CANVAS] Could not find DeviceItem for parent device_id={parent_id}", level="debug")
            else:
                infra_log(f"[CANVAS] on_model_changed: model is not a Pin, type={type(model)}", level="debug")
                if item is None:
                    from ui.items.device import DeviceItem
                    infra_log(f"[CANVAS] Creating DeviceItem for device_id={model_id}", level="debug")
                    print(f"[DIAG] [ADD] Creating DeviceItem for device_id={model_id}")
                    item = DeviceItem(model)
                    self.scene.addItem(item)
                    api.register_scene_item(model_id, item)
                    print(f"[DIAG] [ADD] Added DeviceItem to scene and registered: device_id={model_id}, item={item}")
                    infra_log(f"[CANVAS] Added DeviceItem for device_id={model_id}", level="debug")
                else:
                    print(f"[DIAG] [ADD] DeviceItem already exists for device_id={model_id}: {item}")
                    infra_log(f"[CANVAS] DeviceItem already exists for device_id={model_id}: {item}", level="debug")
        elif action in ('update', 'move'):
            from core.device import Pin
            if isinstance(device, Pin):
                # Update the PinItem for this pin (no direct model mutation)
                pin_item = api.get_scene_item(getattr(device, 'id', None))
                if pin_item is not None and hasattr(pin_item, 'update_from_model'):
                    pin_item.update_from_model()
            else:
                if item is not None:
                    item.model = device
                    if hasattr(item, 'update_from_model'):
                        item.update_from_model()

    def contextMenuEvent(self, event):
        """Show the context menu for the device, pin, wire, or canvas as appropriate."""
        api = APIManager.get_instance()
        scene_pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(scene_pos, self.transform())
        try:
            from ui.items.device import DeviceItem
        except Exception:
            DeviceItem = None
        try:
            from ui.items.wire import WireItem
        except Exception:
            WireItem = None
        try:
            from ui.items.pin import PinItem
        except Exception:
            PinItem = None
        if hasattr(api, 'open_context_menu'):
            if item is not None:
                if DeviceItem and isinstance(item, DeviceItem):
                    api.open_context_menu(event, item=item)
                elif WireItem and isinstance(item, WireItem):
                    api.open_context_menu(event, item=item)
                elif PinItem and isinstance(item, PinItem):
                    api.open_context_menu(event, item=item)
                else:
                    api.open_context_menu(event)
            else:
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
        """Zoom in/out on wheel events, or pass to base handler. Ignores non-QWheelEvent events for robustness."""
        from PySide6.QtGui import QWheelEvent
        if not isinstance(event, QWheelEvent):
            # Ignore synthetic or malformed events (prevents segfaults)
            return
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
        # Subscribe to all API events for robust model sync
        if hasattr(api, 'subscribe_to_all'):
            api.subscribe_to_all(self._on_any_event)

    def _on_any_event(self, event_type, data):
        """Handle any API event that could affect the canvas rendering. Prevent recursion and redundant reloads."""
        # Prevent recursive reloads
        if not hasattr(self, '_is_reloading'):
            self._is_reloading = False
        if self._is_reloading:
            return
        # Only reload for undo/redo, not for every event
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

    def _on_undo_redo_event(self, event_type):
        """Callback for undo/redo events to refresh the canvas scene."""
        if event_type in ("undo", "redo"):
            api = APIManager.get_instance()
            harness = getattr(api.context, 'harness', None)
            if harness is not None:
                self.load_harness(harness)

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