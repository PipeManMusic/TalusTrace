import uuid
from PySide6.QtCore import Qt, QPointF
from tools.base_tool import Tool
from ui.items.pin import PinItem 
from ui.items.wire import GhostWireItem
from core.wire import Wire

class WireTool(Tool):
    def __init__(self):
        super().__init__()
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        self.ghost_wire = None # Use correct class

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self):
        if hasattr(self.api, 'main_window'):
            self.api.main_window.canvas.setCursor(Qt.CrossCursor)

    def _get_pin_at_pos(self, scene_pos):
        if not self.api.main_window: return None, None
        
        # scene_pos is MM, but itemsAt uses scene coords, so it works.
        items = self.api.main_window.canvas.scene.items(scene_pos)
        for item in items:
            if isinstance(item, PinItem):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    return item.pin, device_item.model
        return None, None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        pin, device = self._get_pin_at_pos(event.scene_pos)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                # Use GhostWireItem (handles drawing itself)
                start_pos = self._get_pin_scene_pos(pin)
                self.ghost_wire = GhostWireItem(start_pos, event.scene_pos)
                self.api.main_window.canvas.scene.addItem(self.ghost_wire)
                print(f">> Wire Started from {device.id}:{pin.id}")

        elif self.state == "DRAGGING":
            if pin and device:
                if device == self.start_device and pin == self.start_pin:
                    print(">> Cannot connect pin to itself")
                    return
                self._create_wire(self.start_device, self.start_pin, device, pin)
                self._reset()
            else:
                print(">> Wire Cancelled")
                self._reset()

    def on_mouse_move(self, event):
        if self.state == "DRAGGING" and self.ghost_wire:
            try:
                target_pin, _ = self._get_pin_at_pos(event.scene_pos)
                if target_pin:
                    end_pos = self._get_pin_scene_pos(target_pin)
                else:
                    end_pos = event.scene_pos
                self.ghost_wire.update_target(end_pos)
            except RuntimeError:
                self.ghost_wire = None

    def _create_wire(self, dev1, pin1, dev2, pin2):
        from api.commands.device import AddWireCommand
        
        # No conversions needed! Positions are already MM.
        start_mm = self._get_pin_scene_pos(pin1)
        end_mm = self._get_pin_scene_pos(pin2)
        
        path_nodes = [(start_mm.x(), start_mm.y()), (end_mm.x(), end_mm.y())]

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
        self.api.context.undo_stack.push(cmd)
        print(f">> Wire Created: {wire_id}")

    def _get_pin_scene_pos(self, pin_model):
        scene = self.api.main_window.canvas.scene
        for item in scene.items():
            if isinstance(item, PinItem) and item.pin == pin_model:
                return item.mapToScene(0.0, 0.0)
        return QPointF(0,0)

    def _reset(self):
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        if self.ghost_wire:
            try:
                if self.api.main_window and self.ghost_wire.scene():
                    self.api.main_window.canvas.scene.removeItem(self.ghost_wire)
            except RuntimeError: pass
            self.ghost_wire = None

    def deactivate(self):
        self._reset()
        if hasattr(self.api, 'main_window'):
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)