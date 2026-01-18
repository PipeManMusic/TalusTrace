from infra.undo_stack import BaseCommand
from core.device import Device
from core.wire import Wire
from PySide6.QtCore import QPointF

class MoveCommand(BaseCommand):
    def __init__(self, target, old_x, old_y, new_x, new_y):
        super().__init__("MoveCommand")
        self.target = target
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y
        # Lazy load API
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self, target=None):
        tgt = target if target is not None else self.target
        tgt.x = self.new_x
        tgt.y = self.new_y
        
        # --- RUBBERBANDING LOGIC ---
        self._update_attached_wires(tgt)
        
        self.api.dispatch("model_changed", {"action": "move", "item": tgt})

    def undo(self):
        self.target.x = self.old_x
        self.target.y = self.old_y
        
        # --- RUBBERBANDING LOGIC (Restore) ---
        self._update_attached_wires(self.target)
        
        self.api.dispatch("model_changed", {"action": "move", "item": self.target})

    def _update_attached_wires(self, device):
        """Finds all wires connected to this device and recalculates their endpoints."""
        harness = self.api.context.harness
        
        # 1. Find pins belonging to this device (for offset calculation)
        # Map Pin ID -> (x, y) relative to device
        pin_offsets = {p.id: (p.x, p.y) for p in device.pins}
        
        for wire in harness.wires:
            dirty = False
            
            # Check Start Node
            if wire.from_conn == device.id and wire.from_pin in pin_offsets:
                px, py = pin_offsets[wire.from_pin]
                # Absolute position = Device X + Pin X
                wire.path_nodes[0] = [device.x + px, device.y + py]
                dirty = True
                
            # Check End Node
            if wire.to_conn == device.id and wire.to_pin in pin_offsets:
                px, py = pin_offsets[wire.to_pin]
                wire.path_nodes[-1] = [device.x + px, device.y + py]
                dirty = True
            
            if dirty:
                # Dispatch update for the wire so the renderer redraws it
                self.api.dispatch("model_changed", {"action": "update", "item": wire})

class MoveTool:
    __guide__ = "MoveTool: Handles device and wire movement, ghosting, and drag events."

    def update(self, dx=0, dy=0):
        """Update ghost_item position for test compatibility."""
        if self.ghost_item is not None:
            self.ghost_item.x = self._original_x + dx
            self.ghost_item.y = self._original_y + dy

    def __init__(self):
        self.ghost_item = None
        self._target = None
        self.selected_item = None
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0

    @property
    def api(self):
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self, target=None, selected_item=None, click_pos=None):
        if target:
            self._target = target
            # Store original position for undo/redo
            self._original_x = target.x
            self._original_y = target.y
            # Clone state for ghost
            self.ghost_item = type(target)(**target.model_dump())
            self.selected_item = selected_item

            # Ensure ghost item is visually selected
            if hasattr(self.ghost_item, 'setSelected'):
                try:
                    self.ghost_item.setSelected(True)
                except Exception:
                    pass

            # Ensure the device remains selected in the API
            try:
                from api.manager import APIManager
                api = APIManager.get_instance()
                api.select([target.id], tool_name="MoveTool")
            except Exception:
                pass

            if click_pos:
                self.drag_offset_x = click_pos.x() - target.x
                self.drag_offset_y = click_pos.y() - target.y
            else:
                self.drag_offset_x = 0
                self.drag_offset_y = 0

    def activate(self): pass
    def deactivate(self):
        self.ghost_item = None
        self.selected_item = None

    def on_mouse_press(self, event):
        if hasattr(event, 'scene_item') and event.scene_item:
            item = event.scene_item
            if hasattr(item, 'model') and isinstance(item.model, Device):
                self.start(item.model, item, event.pos_mm)

    def on_mouse_move(self, event):
        if not self.ghost_item: return

        raw_x = event.pos_mm.x()
        raw_y = event.pos_mm.y()

        target_origin_x = raw_x - self.drag_offset_x
        target_origin_y = raw_y - self.drag_offset_y

        snapped_x, snapped_y = self.api.snap_to_grid(target_origin_x, target_origin_y)

        # Only move the ghost item during drag
        self.ghost_item.x = snapped_x
        self.ghost_item.y = snapped_y

        if self.selected_item:
            self.selected_item.setPos(snapped_x, snapped_y)

        # --- Real-time wire endpoint update for ghost device ---
        # Find all wires attached to this device in the scene
        scene = None
        if self.selected_item and hasattr(self.selected_item, 'scene'):
            scene = self.selected_item.scene()
        if scene:
            for item in scene.items():
                # Only update WireItem instances
                from ui.items.wire import WireItem
                if isinstance(item, WireItem):
                    wire = item.model
                    # Check if wire is attached to this device
                    if (hasattr(wire, 'from_conn') and wire.from_conn == self._target.id) or \
                       (hasattr(wire, 'to_conn') and wire.to_conn == self._target.id):
                        # Update endpoints visually to follow ghost
                        pin_offsets = {p.id: (p.x, p.y) for p in self._target.pins}
                        if wire.from_conn == self._target.id and wire.from_pin in pin_offsets:
                            px, py = pin_offsets[wire.from_pin]
                            item.path_nodes[0] = [snapped_x + px, snapped_y + py]
                        if wire.to_conn == self._target.id and wire.to_pin in pin_offsets:
                            px, py = pin_offsets[wire.to_pin]
                            item.path_nodes[-1] = [snapped_x + px, snapped_y + py]
                        item.update_endpoints()

    def on_mouse_release(self, event):
        if self.ghost_item:
            print(f"[MoveTool] Mouse released, attempting to commit move for target: {self._target}")
            cmd = self.commit()
            if cmd:
                print(f"[MoveTool] MoveCommand created: {cmd.description} (from ({cmd.old_x}, {cmd.old_y}) to ({cmd.new_x}, {cmd.new_y}))")
                self.api.context.undo_stack.push(cmd)
            else:
                print("[MoveTool] No move committed (position unchanged or invalid)")
            self.ghost_item = None
            self.selected_item = None

    def commit(self):
        if self._target and self.ghost_item:
            if self._original_x == self.ghost_item.x and self._original_y == self.ghost_item.y:
                return None
            return MoveCommand(self._target, self._original_x, self._original_y, self.ghost_item.x, self.ghost_item.y)
        return None