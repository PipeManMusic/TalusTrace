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
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        self.ghost_line = None

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self):
        if hasattr(self.api, 'main_window'):
            self.api.main_window.canvas.setCursor(Qt.CrossCursor)

    def on_mouse_press(self, event):
        if event.original_event.button() != Qt.LeftButton: return

        # scene_pos is ALREADY in MM. No conversion needed.
        pin, device = self._get_pin_at_pos(event.scene_pos)

        if self.state == "IDLE":
            if pin and device:
                self.start_pin = pin
                self.start_device = device
                self.state = "DRAGGING"
                
                # Visual Feedback
                self.ghost_line = QGraphicsLineItem()
                # Use a cosmetic pen so dashed line stays thin regardless of zoom
                pen = QPen(QColor(0, 255, 0), 0, Qt.DashLine)
                pen.setCosmetic(True)
                self.ghost_line.setPen(pen)
                
                start_pos = self._get_pin_scene_pos(pin, device)
                self.ghost_line.setLine(start_pos.x(), start_pos.y(), event.scene_pos.x(), event.scene_pos.y())
                self.api.main_window.canvas.scene.addItem(self.ghost_line)

        elif self.state == "DRAGGING":
            if pin and device:
                if device == self.start_device and pin == self.start_pin:
                    print(">> Cannot connect pin to itself")
                    return
                self._create_wire(self.start_device, self.start_pin, device, pin)
                self._reset()
            else:
                self._reset()

    def on_mouse_move(self, event):
        if self.state == "DRAGGING" and self.ghost_line:
            if not self.ghost_line.scene(): return
            
            start_pos = self.ghost_line.line().p1()
            target_pin, target_device = self._get_pin_at_pos(event.scene_pos)
            
            if target_pin:
                end_pos = self._get_pin_scene_pos(target_pin, target_device)
            else:
                end_pos = event.scene_pos
            
            self.ghost_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())

    def _create_wire(self, dev1, pin1, dev2, pin2):
        from api.commands.device import AddWireCommand
        
        # 1. Get Geometry in MM
        p1 = self._get_pin_scene_pos(pin1, dev1)
        p2 = self._get_pin_scene_pos(pin2, dev2)

        # 2. Store directly. No math.
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
        self.api.context.undo_stack.push(cmd)

    def _get_pin_at_pos(self, scene_pos):
        """Hit test in World Space (MM)."""
        if not self.api.main_window: return None, None
        
        # scene.items() takes a point in Scene Coordinates (MM)
        items = self.api.main_window.canvas.scene.items(scene_pos)
        for item in items:
            if isinstance(item, PinItem):
                # Ensure we get the parent Device model
                parent = item.parentItem()
                if parent and hasattr(parent, 'model'):
                    return item.pin, parent.model
        return None, None

    def _get_pin_scene_pos(self, pin_model, device_model):
        """Finds the pin item and returns its absolute position in the Scene (MM)."""
        scene = self.api.main_window.canvas.scene
        for item in scene.items():
            if isinstance(item, PinItem) and item.pin.id == pin_model.id:
                # Double check parent to be safe
                parent = item.parentItem()
                if parent and hasattr(parent, 'model') and parent.model.id == device_model.id:
                    return item.mapToScene(0.0, 0.0)
        return QPointF(0,0)

    def _reset(self):
        self.state = "IDLE"
        self.start_pin = None
        self.start_device = None
        if self.ghost_line and self.ghost_line.scene():
            self.api.main_window.canvas.scene.removeItem(self.ghost_line)
        self.ghost_line = None

    def deactivate(self):
        self._reset()
        if hasattr(self.api, 'main_window'):
            self.api.main_window.canvas.setCursor(Qt.ArrowCursor)