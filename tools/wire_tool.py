import uuid
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen, QColor
from tools.base_tool import Tool
from ui.items.pin import PinItem 
from core.wire import Wire

class WireToolState:
    IDLE = "IDLE"
    DRAGGING = "DRAGGING"

class WireTool(Tool):
    def __init__(self, harness=None):
        super().__init__()
        self.harness = harness
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        self.ghost_line = None
        self.current_mouse_pos = QPointF(0, 0)

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    @property
    def scene(self):
        """Robust scene access for Headless/UI modes."""
        if hasattr(self.api, 'scene') and self.api.scene:
            return self.api.scene
        if hasattr(self.api, 'main_window') and self.api.main_window:
            return self.api.main_window.canvas.scene
        return None

    def start(self):
        if hasattr(self.api, 'main_window') and self.api.main_window:
            self.api.main_window.canvas.setCursor(Qt.CrossCursor)

    def _get_pin_at_pos(self, scene_pos):
        """Hit test for PinItem under cursor in World Space (MM)."""
        scene = self.scene
        if not scene: return None, None
        
        # Handle MagicMock vs Real Scene
        items = scene.items(scene_pos)
        
        for item in items:
            if isinstance(item, PinItem):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    return item.pin, device_item.model
        return None, None

    def on_mouse_press(self, event):
        # Determine button safely (Headless vs UI)
        if hasattr(event, 'original_event') and event.original_event:
            if event.original_event.button() != Qt.LeftButton:
                return
        
        pin, device = self._get_pin_at_pos(event.scene_pos)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                # Visual Feedback (Only if UI is present)
                if self.scene:
                    self.ghost_line = QGraphicsLineItem()
                    pen = QPen(QColor(0, 255, 0), 0, Qt.DashLine)
                    pen.setCosmetic(True)
                    self.ghost_line.setPen(pen)
                    start_pos = self._get_pin_scene_pos(pin, device)
                    self.ghost_line.setLine(start_pos.x(), start_pos.y(), event.scene_pos.x(), event.scene_pos.y())
                    self.scene.addItem(self.ghost_line)
            else:
                pass

        elif self.state == "DRAGGING":
            if pin and device:
                if device == self.start_device and pin == self.start_pin:
                    return
                self._create_wire(self.start_device, self.start_pin, device, pin)
                self._reset()
            else:
                self._reset()

    def on_mouse_move(self, event):
        self.current_mouse_pos = event.scene_pos
        
        if self.state == "DRAGGING" and self.ghost_line:
            try:
                if not self.ghost_line.scene(): 
                    self.ghost_line = None
                    return
                
                start_pos = self.ghost_line.line().p1()
                
                # Snap to target pin if hovering
                target_pin, target_device = self._get_pin_at_pos(event.scene_pos)
                if target_pin and target_device:
                    end_pos = self._get_pin_scene_pos(target_pin, target_device)
                else:
                    end_pos = event.scene_pos
                
                self.ghost_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            except RuntimeError:
                self.ghost_line = None

    def _create_wire(self, dev1, pin1, dev2, pin2):
        from api.commands.device import AddWireCommand
        p1 = self._get_pin_scene_pos(pin1, dev1)
        p2 = self._get_pin_scene_pos(pin2, dev2)
        
        path_nodes = [[p1.x(), p1.y()], [p2.x(), p2.y()]]
        wire_id = f"W_{str(uuid.uuid4())[:8]}"
        new_wire = Wire(
            id=wire_id,
            from_conn=dev1.id,
            from_pin=pin1.id,
            to_conn=dev2.id,
            to_pin=pin2.id,
            type="STANDARD",
            path_nodes=path_nodes
        )
        cmd = AddWireCommand(new_wire)
        if hasattr(self.api.context, 'undo_stack'):
            self.api.context.undo_stack.push(cmd)
        
        # Reset tool
        if hasattr(self.api.tool_manager, 'set_tool'):
            self.api.tool_manager.set_tool('select')

    def _get_pin_scene_pos(self, pin_model, device_model):
        scene = self.scene
        if not scene: return QPointF(0,0)
        
        # Logic for Headless Mocking support
        if hasattr(scene, 'items'):
            for item in scene.items():
                if isinstance(item, PinItem) and hasattr(item, 'pin') and item.pin.id == pin_model.id:
                    # In headless, mapToScene might be mocked or we accept item pos
                    if hasattr(item, 'mapToScene'):
                        return item.mapToScene(0.0, 0.0)
                    return item.pos()
        return QPointF(0,0)

    def _reset(self):
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        
        if self.ghost_line:
            try:
                if self.scene and self.ghost_line.scene() == self.scene:
                    self.scene.removeItem(self.ghost_line)
            except RuntimeError:
                pass
            self.ghost_line = None

    def deactivate(self):
        self._reset()
        if hasattr(self.api, 'main_window') and self.api.main_window:
            from PySide6.QtCore import Qt
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)