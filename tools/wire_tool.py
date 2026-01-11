import uuid
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsLineItem
from PySide6.QtGui import QPen, QColor
from tools.base_tool import Tool
from ui.items.pin import PinItem 
from core.wire import Wire

class WireTool(Tool):
    def __init__(self):
        super().__init__()
        self.state = "IDLE"  # IDLE | DRAGGING
        self.start_pin = None
        self.start_device = None
        self.ghost_line = None
        self.current_mouse_pos = QPointF(0, 0)

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self):
        if hasattr(self.api, 'main_window'):
            self.api.main_window.canvas.setCursor(Qt.CrossCursor)

    def _get_pin_at_pos(self, scene_pos):
        """Hit test for PinItem under cursor (Requires PIXEL coords)."""
        if not self.api.main_window: return None, None
        
        # Check visuals (Scene Coordinates)
        items = self.api.main_window.canvas.scene.items(scene_pos)
        for item in items:
            if isinstance(item, PinItem):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    return item.pin, device_item.model
        return None, None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        # 1. Hit Test for Pin using Pixels (scene_pos)
        pin, device = self._get_pin_at_pos(event.scene_pos)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                self.ghost_line = QGraphicsLineItem()
                self.ghost_line.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
                
                pin_item_pos = self._get_pin_scene_pos(pin)
                # Draw ghost line using Pixel coordinates
                self.ghost_line.setLine(pin_item_pos.x(), pin_item_pos.y(), event.scene_pos.x(), event.scene_pos.y())
                self.api.main_window.canvas.scene.addItem(self.ghost_line)
                print(f">> Wire Started from {device.id}:{pin.id}")

        elif self.state == "DRAGGING":
            if pin and device:
                if device == self.start_device and pin == self.start_pin:
                    print(">> Cannot connect pin to itself")
                    return
                
                self._create_wire(self.start_device, self.start_pin, device, pin)
                self._reset()
            else:
                print(">> Wire Cancelled (No target pin)")
                self._reset()

    def on_mouse_move(self, event):
        self.current_mouse_pos = event.scene_pos
        
        if self.state == "DRAGGING" and self.ghost_line:
            # Check if ghost_line is still valid (it might be deleted if scene cleared)
            try:
                if not self.ghost_line.scene(): return
                start_pos = self.ghost_line.line().p1()
                
                # Hit test target using Pixels
                target_pin, _ = self._get_pin_at_pos(event.scene_pos)
                if target_pin:
                    end_pos = self._get_pin_scene_pos(target_pin)
                else:
                    end_pos = event.scene_pos
                
                self.ghost_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
            except RuntimeError:
                self.ghost_line = None

    def _create_wire(self, dev1, pin1, dev2, pin2):
        from api.commands.device import AddWireCommand
        
        wire_id = f"W_{str(uuid.uuid4())[:8]}"
        
        new_wire = Wire(
            id=wire_id,
            from_conn=dev1.id,
            from_pin=pin1.id,
            to_conn=dev2.id,
            to_pin=pin2.id,
            type="STANDARD"
        )
        
        cmd = AddWireCommand(new_wire)
        self.api.context.undo_stack.push(cmd)
        print(f">> Wire Created: {wire_id}")

    def _get_pin_scene_pos(self, pin_model):
        """Returns the Pixel position of a pin."""
        scene = self.api.main_window.canvas.scene
        for item in scene.items():
            if isinstance(item, PinItem) and item.pin == pin_model:
                # Map 0,0 (center of pin) to scene
                return item.mapToScene(0.0, 0.0)
        return QPointF(0,0)

    def _reset(self):
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        if self.ghost_line:
            # FIXED: Handle case where scene.clear() (triggered by _create_wire -> refresh)
            # has already deleted the C++ object.
            try:
                if self.api.main_window and self.ghost_line.scene():
                    self.api.main_window.canvas.scene.removeItem(self.ghost_line)
            except RuntimeError:
                pass # Object already deleted, safe to ignore
            self.ghost_line = None

    def deactivate(self):
        self._reset()
        if hasattr(self.api, 'main_window'):
            from PySide6.QtCore import Qt
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)