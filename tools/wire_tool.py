import math
from enum import Enum, auto
from tools.base import BaseTool
from core.wire import Wire
from ui.items import GhostWireItem, BundleItem, PinItem
from PySide6.QtCore import QPointF

class WireToolState(Enum):
    IDLE = auto()
    DRAGGING = auto()

class WireTool(BaseTool):
    GRID_SIZE_MM = 25.0
    def _snap_to_grid(self, x, y):
        grid = self.GRID_SIZE_MM
        import math
        return (math.floor(x / grid) * grid, math.floor(y / grid) * grid)
    def on_mouse_move(self, event):
        # Snap coordinates to grid before updating model/ghost
        if hasattr(event, 'pos_mm'):
            x, y = event.pos_mm.x(), event.pos_mm.y()
            x, y = self._snap_to_grid(x, y)
            # Update ghost wire or model as needed
            if self.ghost_item and hasattr(self.ghost_item, 'setEndPoint'):
                self.ghost_item.setEndPoint(x, y)
            # If dragging a wire segment, update the model
            # (Add your wire segment update logic here as needed)

    def on_mouse_double_click(self, event):
        # Allow adding elbow points to existing wires (BundleItem)
        if isinstance(event.scene_item, BundleItem):
            bundle = event.scene_item
            # Insert elbow before the last node (keep end-pin connection)
            if hasattr(bundle, 'path_nodes') and isinstance(bundle.path_nodes, list) and len(bundle.path_nodes) >= 2:
                # Insert at -1 (before last)
                new_point = (event.pos_mm.x(), event.pos_mm.y())
                bundle.path_nodes.insert(-1, new_point)
                # Rebuild the QPainterPath
                qpath = bundle.path()
                qpath = qpath.__class__()  # New QPainterPath
                qpath.moveTo(*bundle.path_nodes[0])
                for node in bundle.path_nodes[1:]:
                    qpath.lineTo(*node)
                bundle.setPath(qpath)
                # Refresh compliance visuals if available
                if hasattr(bundle, 'update_compliance_visuals'):
                    bundle.update_compliance_visuals()
                # Optionally, force a redraw
                bundle.update()

    SNAP_DISTANCE_MM = 8.0

    def __init__(self, context=None):
        self.state = WireToolState.IDLE
        self.start_device = None
        self.start_pin = None
        self.ghost_item = None
        self._test_harness = context 

    # --- Test Helper ---
    def on_click(self, device_id, pin_id):
        """Simulates a click for unit tests."""
        harness = self._get_harness()
        devices = harness.devices if hasattr(harness, 'devices') else []
        
        found_dev = next((d for d in devices if d.id == device_id), None)
        if not found_dev: return
        
        found_pin = next((p for p in found_dev.pins if p.id == pin_id), None)
        if not found_pin: return
        
        # Inject state logic
        if self.state == WireToolState.IDLE:
            self.start_device = found_dev
            self.start_pin = found_pin
            self.state = WireToolState.DRAGGING
        elif self.state == WireToolState.DRAGGING:
             # FIX: If clicking the same pin, do nothing (Stay Dragging)
             if found_dev == self.start_device and found_pin == self.start_pin:
                 return

             self._create_wire(found_dev, found_pin, None)
             self.deactivate()

    def activate(self):
        print(">> Wire Tool: Active. Click a pin to start.")

    def deactivate(self):
        self._clear_ghost()
        self.state = WireToolState.IDLE

    def _get_harness(self):
        if self._test_harness:
            return self._test_harness
        from api.manager import APIManager
        return APIManager.get_instance().context.harness

    def on_mouse_press(self, event):
        device, pin = None, None
        # Prioritize PinItem hits for DRAGGING state
        if self.state == WireToolState.DRAGGING and isinstance(event.scene_item, PinItem):
            device_item = event.scene_item.parentItem()
            device = device_item.device
            pin = event.scene_item.pin
            print(f">> Visual Hit: {device.id}:{pin.id}")
        elif isinstance(event.scene_item, PinItem):
            device_item = event.scene_item.parentItem()
            device = device_item.device
            pin = event.scene_item.pin
            print(f">> Visual Hit: {device.id}:{pin.id}")
        else:
            device, pin = self._find_pin_at(event.pos_mm)

        if self.state == WireToolState.IDLE:
            if device and pin:
                print(f">> Wire Start: {device.id}:{pin.id}")
                self.start_device = device
                self.start_pin = pin
                self.state = WireToolState.DRAGGING
                
                if hasattr(event, 'scene') and event.scene:
                     self.ghost_item = GhostWireItem(
                        QPointF(device.x + pin.x, device.y + pin.y),
                        event.pos_mm
                    )
                     event.scene.addItem(self.ghost_item)
        
        elif self.state == WireToolState.DRAGGING:
            if device and pin:
                if device == self.start_device and pin == self.start_pin:
                    return 
                print(f">> Wire End: {device.id}:{pin.id}")
                self._create_wire(device, pin, getattr(event, 'scene', None))
                self.deactivate() 
            else:
                print(">> Wire Cancelled (No pin found)")
                self.deactivate()

    def on_mouse_move(self, event):
        if self.state == WireToolState.DRAGGING and self.ghost_item:
            self.ghost_item.update_target(event.pos_mm)

    def _find_pin_at(self, pos_mm):
        harness = self._get_harness()
        closest_dist = self.SNAP_DISTANCE_MM
        found = (None, None)
        devices = harness.devices if hasattr(harness, 'devices') else []
        for device in devices:
            for pin in device.pins:
                pin_world_x = device.x + pin.x
                pin_world_y = device.y + pin.y
                dx = pos_mm.x() - pin_world_x
                dy = pos_mm.y() - pin_world_y
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < closest_dist:
                    closest_dist = dist
                    found = (device, pin)
        return found

    def _create_wire(self, end_device, end_pin, scene):
        harness = self._get_harness()
        wires_list = harness.wires if hasattr(harness, 'wires') else []
        
        new_wire = Wire(
            id=f"W-{len(wires_list)+1:03d}",
            from_conn=self.start_device.id,
            from_pin=self.start_pin.id,
            to_conn=end_device.id,
            to_pin=end_pin.id
        )
        wires_list.append(new_wire)
        
        if scene:
            start_pt = (self.start_device.x + self.start_pin.x, self.start_device.y + self.start_pin.y)
            end_pt = (end_device.x + end_pin.x, end_device.y + end_pin.y)
            visual = BundleItem([start_pt, end_pt], wire_diameters=[1.0], wire_model=new_wire)
            scene.addItem(visual)
        
        print(f">> Wire Created: {new_wire.id}")
    
    def _clear_ghost(self):
        if self.ghost_item:
            scene = self.ghost_item.scene()
            if scene: scene.removeItem(self.ghost_item)
            self.ghost_item = None