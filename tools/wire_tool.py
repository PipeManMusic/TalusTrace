import math
from PySide6.QtCore import QPointF
from tools.base import BaseTool
from core.wire import Wire
from ui.items import GhostWireItem, BundleItem

class WireTool(BaseTool):
    SNAP_DISTANCE_MM = 5.0

    def __init__(self):
        self.state = "IDLE"
        self.start_device = None
        self.start_pin = None
        self.ghost_item = None

    def activate(self):
        print(">> Wire Tool: Active. Click a pin to start.")

    def deactivate(self):
        self._clear_ghost()
        self.state = "IDLE"

    def on_mouse_press(self, event):
        # 1. Try to find a pin under the mouse
        device, pin = self._find_pin_at(event.pos_mm, event.scene_item)

        if self.state == "IDLE":
            if device and pin:
                print(f">> Wire Start: {device.id}:{pin.id}")
                self.start_device = device
                self.start_pin = pin
                self.state = "DRAGGING"
                
                # Create Visual Ghost
                # (Hack: Access scene via event context if possible, or assume active view)
                if hasattr(event.original_event, 'widget'):
                    scene = event.original_event.widget().parent().scene
                    self.ghost_item = GhostWireItem(
                        QPointF(device.x + pin.x, device.y + pin.y),
                        event.pos_mm
                    )
                    scene.addItem(self.ghost_item)
        
        elif self.state == "DRAGGING":
            if device and pin:
                if device == self.start_device and pin == self.start_pin:
                    return # Ignore clicking the same pin
                
                print(f">> Wire End: {device.id}:{pin.id}")
                self._create_wire(device, pin, self.ghost_item.scene())
                self.deactivate() 
            else:
                print(">> Wire Cancelled (Clicked empty space)")
                self.deactivate()

    def on_mouse_move(self, event):
        if self.state == "DRAGGING" and self.ghost_item:
            self.ghost_item.update_target(event.pos_mm)

    def _find_pin_at(self, pos_mm, scene_item):
        if not scene_item or not hasattr(scene_item, 'device'):
            return None, None

        device = scene_item.device
        local_x = pos_mm.x() - device.x
        local_y = pos_mm.y() - device.y

        for pin in device.pins:
            dx = local_x - pin.x
            dy = local_y - pin.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist <= self.SNAP_DISTANCE_MM:
                return device, pin
        
        return None, None

    def _create_wire(self, end_device, end_pin, scene):
        from api.manager import APIManager
        harness = APIManager.get_instance().context.harness
        
        # 1. Create Model
        new_wire = Wire(
            id=f"W-{len(harness.wires)+1:03d}",
            from_conn=self.start_device.id,
            from_pin=self.start_pin.id,
            to_conn=end_device.id,
            to_pin=end_pin.id
        )
        harness.wires.append(new_wire)
        
        # 2. Update Visuals
        start_pt = (self.start_device.x + self.start_pin.x, self.start_device.y + self.start_pin.y)
        end_pt = (end_device.x + end_pin.x, end_device.y + end_pin.y)
        
        visual = BundleItem([start_pt, end_pt], wire_diameters=[1.0])
        scene.addItem(visual)
        
        print(f">> Wire Created: {new_wire.id}")
    
    def _clear_ghost(self):
        if self.ghost_item:
            scene = self.ghost_item.scene()
            if scene:
                scene.removeItem(self.ghost_item)
            self.ghost_item = None