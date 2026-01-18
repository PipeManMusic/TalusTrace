
import math
import os
import yaml
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QMenu, QGraphicsItem
from PySide6.QtGui import QPainter, QBrush, QPen, QMouseEvent, QAction, QCursor
from PySide6.QtCore import Qt, QLineF
from api.manager import APIManager
from api.actions import registry
from ui.theme import ThemeManager
from ui.items.device import DeviceItem
from ui.items.wire import WireItem, TwistedPairItem
from ui.items.pin import PinItem # Import for hover check

class HarnessCanvas(QGraphicsView):
    def zoom_extents(self):
        """
        Fits all items in the scene into the view. Used for test compatibility.
        """
        scene_rect = self.scene.itemsBoundingRect() if self.scene else None
        if scene_rect and not scene_rect.isNull():
            self.fitInView(scene_rect, Qt.KeepAspectRatio)
        else:
            # Fallback: fit the whole scene rect
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

class CanvasEvent:
    def __init__(self, view_event, scene_pos, scene, scene_item=None):
        self.original_event = view_event
        self.scene_pos = scene_pos
        self.pos_mm = scene_pos
        self.scene = scene
        if scene_item is not None:
            self.scene_item = scene_item
        elif scene is not None:
            self.scene_item = scene.itemAt(scene_pos, QGraphicsView().transform())
        else:
            self.scene_item = None

class HarnessCanvas(QGraphicsView):
    def _resolve_pin_coords(self, device_id, pin_id):
        """
        Robustly find the global scene coordinates of a pin by checking 
        the local DeviceItem registry and its children.
        """
        dev_item = self.device_items.get(device_id)
        if not dev_item:
            return None
        from ui.items.pin import PinItem
        for child in dev_item.childItems():
            if isinstance(child, PinItem) and hasattr(child, 'model'):
                if str(child.model.id) == str(pin_id):
                    pos = child.scenePos()
                    return [pos.x(), pos.y()]
        return None
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.theme = ThemeManager() 
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self._update_view_scale()
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        self._apply_theme()
        self.context_menu_config = self._load_context_menu_config()

        # Model ID to QGraphicsItem mapping for incremental updates
        self.device_items = {}  # device_id -> DeviceItem
        self.wire_items = {}    # wire_id -> WireItem
        self.pin_items = {}     # pin_id -> PinItem

        # Subscribe to fine-grained model events
        self.api.subscribe("device_added", self.on_device_added)
        self.api.subscribe("device_removed", self.on_device_removed)
        self.api.subscribe("device_updated", self.on_device_updated)
        self.api.subscribe("wire_added", self.on_wire_added)
        self.api.subscribe("wire_removed", self.on_wire_removed)
        self.api.subscribe("wire_updated", self.on_wire_updated)
        self.api.subscribe("pin_added", self.on_pin_added)
        self.api.subscribe("pin_removed", self.on_pin_removed)
    def on_pin_added(self, pin):
        # Find parent device item
        parent_device_id = getattr(pin, 'device_id', None)
        parent_item = self.device_items.get(parent_device_id)
        if parent_item:
            pin_item = PinItem(pin, parent_item)
            pin_item.setPos(pin.x, pin.y)
            self.pin_items[pin.id] = pin_item
            # No need to add to scene; parented to device

    def on_pin_removed(self, pin):
        pin_item = self.pin_items.pop(pin.id, None)
        if pin_item:
            if pin_item.scene():
                pin_item.scene().removeItem(pin_item)
            pin_item.setParentItem(None)
            if hasattr(pin_item, 'cleanup'):
                pin_item.cleanup()

    def on_device_updated(self, device):
        dev_item = self.device_items.get(device.id)
        if dev_item:
            # Remove all old PinItems (use API registry)
            for pin_id in list(self.pin_items.keys()):
                pin_item = self.pin_items[pin_id]
                if getattr(pin_item, 'parentItem', lambda: None)() == dev_item:
                    if pin_item.scene():
                        pin_item.scene().removeItem(pin_item)
                    pin_item.setParentItem(None)
                    if hasattr(pin_item, 'cleanup'):
                        pin_item.cleanup()
                    self.api.unregister_scene_item(pin_id)
                    self.pin_items.pop(pin_id, None)
            # Re-add pins from device model
            if hasattr(device, 'pins'):
                for pin in device.pins:
                    pin_item = PinItem(pin, dev_item)
                    pin_item.setPos(pin.x, pin.y)
                    self.pin_items[pin.id] = pin_item
                    self.api.register_scene_item(pin.id, pin_item)
            # Optionally update device visuals here
            if hasattr(dev_item, 'update_from_model'):
                dev_item.update_from_model(device)

        # Fallback: full reload on generic model change
        self.api.subscribe("model_changed", self.refresh)
        self.api.subscribe("theme_changed", self._on_theme_changed)
        self.api.subscribe("settings_changed", self._on_settings_changed)

    # --- Event-driven handlers ---
    def on_device_added(self, device):
        from ui.items.device import DeviceItem
        from ui.items.pin import PinItem
        dev_item = DeviceItem(device)
        self.scene.addItem(dev_item)
        self.device_items[device.id] = dev_item
        # Register DeviceItem
        self.api.register_scene_item(device.id, dev_item)
        # Register all PinItems
        if hasattr(device, 'pins'):
            for pin in device.pins:
                pin_item = PinItem(pin, dev_item)
                pin_item.setPos(pin.x, pin.y)
                self.pin_items[pin.id] = pin_item
                self.api.register_scene_item(pin.id, pin_item)

    def on_device_removed(self, device):
        dev_item = self.device_items.pop(device.id, None)
        if dev_item:
            self.scene.removeItem(dev_item)
            dev_item.cleanup() if hasattr(dev_item, 'cleanup') else None
            self.api.unregister_scene_item(device.id)
    def on_device_updated(self, device):
        dev_item = self.device_items.get(device.id)
        if dev_item:
            dev_item.update_from_model(device) if hasattr(dev_item, 'update_from_model') else None

    def on_wire_added(self, wire):
        print(f"[HarnessCanvas.on_wire_added] Adding wire: {getattr(wire, 'id', None)}")
        from ui.items.wire import WireItem, TwistedPairItem
        pin_lookup_fn = self._resolve_pin_coords
        if not getattr(wire, 'path_nodes', None) or len(wire.path_nodes) < 2:
            from_pos = pin_lookup_fn(wire.from_conn, wire.from_pin)
            to_pos = pin_lookup_fn(wire.to_conn, wire.to_pin)
            if from_pos and to_pos:
                wire.path_nodes = [from_pos, to_pos]
                print(f"[INFO] Auto-generated path_nodes for wire {getattr(wire, 'id', None)}")
            else:
                print(f"[WARNING] Could not determine endpoints for wire. Defaulting to (0,0).")
                wire.path_nodes = [[0, 0], [0, 0]]
        is_twisted = getattr(wire, 'type', 'STANDARD') == 'TWISTED_PAIR'
        if is_twisted:
            item = TwistedPairItem(wire.path_nodes, getattr(wire, 'diameter_mm', 1.0))
        else:
            item = WireItem(wire, pin_lookup=pin_lookup_fn)
        if item:
            self.scene.addItem(item)
            self.wire_items[wire.id] = item
            self.api.register_scene_item(wire.id, item)
            if hasattr(item, 'update_endpoints'):
                item.update_endpoints()
            def wire_update_handler(updated_wire):
                if hasattr(item, 'update_from_model'):
                    item.update_from_model(updated_wire)
                elif hasattr(item, 'update_endpoints'):
                    item.update_endpoints()
                if hasattr(item, 'update'):
                    item.update()
            handler_name = f"_wire_update_handler_{wire.id}"
            setattr(self, handler_name, wire_update_handler)
            self.api.subscribe("wire_updated", getattr(self, handler_name))
        if item:
            self.scene.addItem(item)
            self.wire_items[wire.id] = item
            # Register in API scene registry
            self.api.register_scene_item(wire.id, item)
            if hasattr(item, 'update_endpoints'):
                item.update_endpoints()
            # Subscribe to model update events for this wire
            def wire_update_handler(updated_wire):
                if hasattr(item, 'update_from_model'):
                    item.update_from_model(updated_wire)
                elif hasattr(item, 'update_endpoints'):
                    item.update_endpoints()
                if hasattr(item, 'update'):
                    item.update()
            # Use a unique handler per wire to avoid cross-updates
            handler_name = f"_wire_update_handler_{wire.id}"
            setattr(self, handler_name, wire_update_handler)
            self.api.subscribe("wire_updated", getattr(self, handler_name))

    def on_wire_removed(self, wire):
        item = self.wire_items.pop(wire.id, None)
        if item:
            self.scene.removeItem(item)
            item.cleanup() if hasattr(item, 'cleanup') else None

    def on_wire_updated(self, wire):
        item = self.wire_items.get(wire.id)
        if item and hasattr(item, 'update_from_model'):
            item.update_from_model(wire)
        elif item and hasattr(item, 'update_endpoints'):
            item.update_endpoints()

    # TODO: Add similar handlers for pins, etc.

    # ... (Load methods remain the same) ...
    def _load_context_menu_config(self):
        path = os.path.join("resources", "config", "ui_layout.yaml")
        if not os.path.exists(path): return {}
        try:
            with open(path, 'r') as f: return yaml.safe_load(f).get("context_menu", {})
        except: return {}

    def _update_view_scale(self):
        # Only reset transform when DPI or grid size changes
        dpi = getattr(self.api.settings, 'pixels_per_inch', 96.0)
        self.pixels_per_mm = dpi / 25.4
        self.resetTransform()
        self.scale(self.pixels_per_mm, self.pixels_per_mm)

    def wheelEvent(self, event):
        # Smooth zooming: scale view incrementally
        zoom_factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1/zoom_factor, 1/zoom_factor)
        event.accept()

    def _apply_theme(self):
        self.theme = ThemeManager() 
        bg_color = self.theme.get_color("canvas_bg")
        self.setBackgroundBrush(QBrush(bg_color))

    def _on_theme_changed(self, data):
        self._apply_theme(); self.scene.update()
    def _on_settings_changed(self, data):
        self._update_view_scale(); self.scene.update()
    def refresh(self, data):
        self.load_harness(self.api.context.harness)

    def load_harness(self, harness):
        # Clean up all WireItems before clearing the scene
        for item in self.scene.items():
            try:
                from ui.items.wire import WireItem
                if isinstance(item, WireItem):
                    item.cleanup()
            except Exception:
                pass
        self.scene.clear()
        self.device_items = {}
        self.pin_items = {}
        self.wire_items = {}
        if not harness: return
        from ui.items.device import DeviceItem
        from ui.items.pin import PinItem
        for device in harness.devices:
            dev_item = DeviceItem(device)
            self.scene.addItem(dev_item)
            self.device_items[device.id] = dev_item
            self.api.register_scene_item(device.id, dev_item)
            if hasattr(device, 'pins'):
                for pin in device.pins:
                    for child in dev_item.childItems():
                        if isinstance(child, PinItem) and getattr(child.model, 'id', None) == pin.id:
                            self.pin_items[pin.id] = child
                            self.api.register_scene_item(pin.id, child)
        from ui.items.wire import WireItem, TwistedPairItem
        pin_lookup_fn = self._resolve_pin_coords
        for wire in harness.wires:
            is_twisted = getattr(wire, 'type', 'STANDARD') == 'TWISTED_PAIR'
            if not getattr(wire, 'path_nodes', None) or len(wire.path_nodes) < 2:
                from_pos = pin_lookup_fn(wire.from_conn, wire.from_pin)
                to_pos = pin_lookup_fn(wire.to_conn, wire.to_pin)
                if from_pos and to_pos:
                    wire.path_nodes = [from_pos, to_pos]
                else:
                    wire.path_nodes = [[0, 0], [0, 0]]
            if is_twisted:
                item = TwistedPairItem(wire.path_nodes, getattr(wire, 'diameter_mm', 1.0))
            else:
                item = WireItem(wire, pin_lookup=pin_lookup_fn)
            if item:
                self.scene.addItem(item)
                self.wire_items[wire.id] = item
                self.api.register_scene_item(wire.id, item)
                if hasattr(item, 'update_endpoints'):
                    item.update_endpoints()

    # --- INPUT HANDLING ---
    def mouseMoveEvent(self, event):
        # 1. Update Tools
        self.api.input_system.handle_canvas_event(self._create_tool_event(event))
        
        # 2. Handle Cursors (Visual Feedback)
        # Only override if no specific tool is forcing a cursor (like WireTool drawing)
        current_tool_id = getattr(self.api.tool_manager, 'current_tool_id', 'select')
        
        if current_tool_id == 'select':
            pos = self.mapToScene(event.pos())
            items = self.scene.items(pos)
            
            cursor_set = False
            for item in items:
                if isinstance(item, PinItem):
                    self.setCursor(Qt.CrossCursor)
                    cursor_set = True
                    break
                elif isinstance(item, DeviceItem):
                    self.setCursor(Qt.OpenHandCursor)
                    cursor_set = True
                    break
            
            if not cursor_set:
                self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def _create_tool_event(self, event: QMouseEvent):
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos) 
        return CanvasEvent(event, scene_pos, self.scene)

    def mousePressEvent(self, event):
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        scene_pos = self.mapToScene(pos)
        item = self.scene.itemAt(scene_pos, self.transform())

        if not hasattr(self, '_wire_drawing_state'):
            self._wire_drawing_state = {'active': False, 'start_pin': None}

        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake)
            return

        if event.button() == Qt.RightButton:
            self.contextMenuEvent(event)
            return

        from ui.items.pin import PinItem
        if event.button() == Qt.LeftButton:
            if isinstance(item, PinItem):
                # Activate WireTool if not already active
                if self.api.tool_manager.active_tool != self.api.tool_manager.get_tool('wire'):
                    self.api.tool_manager.set_tool('wire')
                # Forward event to active tool (WireTool)
                self.api.input_system.handle_canvas_event(self._create_tool_event(event))
                return
            # Otherwise, normal selection/move logic
            self.api.input_system.handle_canvas_event(self._create_tool_event(event))
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton: self.setDragMode(QGraphicsView.NoDrag)
        self.api.input_system.handle_canvas_event(self._create_tool_event(event))
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # FIX: Ignore Undo/Redo keys here so they bubble to MainWindow
        from PySide6.QtGui import QKeySequence
        if event.matches(QKeySequence.Undo) or (event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z):
            event.ignore()
            return
        super().keyPressEvent(event)

    # ... (Rest of drawing methods) ...
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
            lines.append(QLineF(x, rect.top(), x, rect.bottom())); x += grid_mm
        y = top
        while y < rect.bottom():
             lines.append(QLineF(rect.left(), y, rect.right(), y)); y += grid_mm
        painter.drawLines(lines)
        
    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        menu_type = None
        # Only keep valid (not deleted) QGraphicsItems in prev_selection
        prev_selection = []
        for sel in self.scene.selectedItems():
            try:
                if sel.scene() is not None:
                    prev_selection.append(sel)
            except RuntimeError:
                # The C++ object has been deleted, skip
                continue
        from core.selection import SelectionManager
        prev_core_selection = SelectionManager().selected_models[:]
        temp_selected = False
        if item:
            # Always set the item's model as the selection in SelectionManager
            if hasattr(item, 'model'):
                SelectionManager().set_selection([item.model])
            # Select the item under the cursor if not already selected
            if hasattr(item, 'setSelected') and not item.isSelected():
                # Deselect others if not multi-select
                for sel in self.scene.selectedItems():
                    sel.setSelected(False)
                item.setSelected(True)
                temp_selected = True
            if hasattr(item, 'pin'):
                menu_type = 'pin'
            elif hasattr(item, 'model'):
                menu_type = type(item.model).__name__.lower()
        if not menu_type or menu_type not in self.context_menu_config:
            return
        menu = QMenu(self)
        actions = []
        for entry in self.context_menu_config[menu_type]:
            if entry.get("separator"):
                menu.addSeparator()
            elif entry.get("command"):
                cmd_id = entry["command"]
                label = cmd_id.split(".")[-1].replace("_", " ").title()
                action = QAction(label, self)
                # Wrap the command execution to restore selection after the command
                def make_triggered(cmd_id, item=item, prev_selection=prev_selection, temp_selected=temp_selected, prev_core_selection=prev_core_selection):
                    def triggered():
                        registry.execute(cmd_id)
                        if temp_selected:
                            try:
                                if item.scene() is not None:
                                    item.setSelected(False)
                            except RuntimeError:
                                pass  # Item already deleted
                            for sel in prev_selection:
                                try:
                                    if sel.scene() is not None:
                                        sel.setSelected(True)
                                except RuntimeError:
                                    continue  # Skip deleted
                            # Restore core selection
                            from core.selection import SelectionManager
                            SelectionManager().set_selection([s.model for s in prev_selection if hasattr(s, 'model')])
                        else:
                            # If not temp, restore core selection anyway (no-op if unchanged)
                            from core.selection import SelectionManager
                            SelectionManager().set_selection([s.model for s in prev_selection if hasattr(s, 'model')])
                    return triggered
                action.triggered.connect(make_triggered(cmd_id))
                menu.addAction(action)
                actions.append(action)
        menu.exec_(event.globalPos())