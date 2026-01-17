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
        self._update_view_scale()
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.scene.setSceneRect(-50000, -50000, 100000, 100000)
        
        self._apply_theme()
        self.context_menu_config = self._load_context_menu_config()
        
        self.api.subscribe("model_changed", self.refresh)
        self.api.subscribe("theme_changed", self._on_theme_changed)
        self.api.subscribe("settings_changed", self._on_settings_changed)

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
        if not harness: return
        device_items = {}
        for device in harness.devices:
            dev_item = DeviceItem(device)
            self.scene.addItem(dev_item)
            device_items[device.id] = dev_item
        wire_items = []
        for wire in harness.wires:
            if not (wire.from_conn and wire.to_conn): continue
            item = TwistedPairItem(wire.path_nodes, getattr(wire, 'diameter_mm', 1.0)) if getattr(wire, 'type', 'STANDARD') == 'TWISTED_PAIR' else WireItem(wire)
            if item:
                self.scene.addItem(item)
                wire_items.append(item)
        # After all items are added, update wire endpoints to glue to pins
        for wire_item in wire_items:
            if hasattr(wire_item, 'update_endpoints'):
                wire_item.update_endpoints()

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