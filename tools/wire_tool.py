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
        """Hit test for PinItem under cursor."""
        if not self.api.main_window: return None, None
        
        items = self.api.main_window.canvas.scene.items(scene_pos)
        for item in items:
            if isinstance(item, PinItem):
                device_item = item.parentItem()
                if device_item and hasattr(device_item, 'model'):
                    return item.pin, device_item.model
        return None, None

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        # 1. Hit Test for Pin
        pin, device = self._get_pin_at_pos(event.pos_mm)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                self.ghost_line = QGraphicsLineItem()
                self.ghost_line.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
                
                pin_item_pos = self._get_pin_scene_pos(pin)
                self.ghost_line.setLine(pin_item_pos.x(), pin_item_pos.y(), event.pos_mm.x(), event.pos_mm.y())
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
        self.current_mouse_pos = event.pos_mm
        
        if self.state == "DRAGGING" and self.ghost_line:
            start_pos = self.ghost_line.line().p1()
            
            target_pin, _ = self._get_pin_at_pos(event.pos_mm)
            if target_pin:
                end_pos = self._get_pin_scene_pos(target_pin)
            else:
                end_pos = event.pos_mm
            
            self.ghost_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())

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
        scene = self.api.main_window.canvas.scene
        for item in scene.items():
            if isinstance(item, PinItem) and item.pin == pin_model:
                return item.mapToScene(1.0, 1.0)
        return QPointF(0,0)

    def _reset(self):
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        if self.ghost_line:
            if self.api.main_window:
                self.api.main_window.canvas.scene.removeItem(self.ghost_line)
            self.ghost_line = None

    def deactivate(self):
        self._reset()
        if hasattr(self.api, 'main_window'):
            from PySide6.QtCore import Qt
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)
