from infra.undo_stack import BaseCommand
from core.device import Device

class MoveCommand(BaseCommand):
    def __init__(self, target, new_x, new_y):
        super().__init__("MoveCommand")
        self.target = target
        self.new_x = new_x
        self.new_y = new_y
        self.old_x = target.x
        self.old_y = target.y
        # Lazy load API
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self, target=None):
        tgt = target if target is not None else self.target
        tgt.x = self.new_x
        tgt.y = self.new_y
        self.api.dispatch("model_changed", {"action": "move", "item": tgt})

    def undo(self):
        self.target.x = self.old_x
        self.target.y = self.old_y
        self.api.dispatch("model_changed", {"action": "move", "item": self.target})

class MoveTool:
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
            self.ghost_item = type(target)(**target.model_dump())
            self.selected_item = selected_item
            
            # FIX: Calculate grab offset
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
        
        # 1. Raw Mouse Position
        raw_x = event.pos_mm.x()
        raw_y = event.pos_mm.y()
        
        # 2. Correct for Grab Offset
        target_origin_x = raw_x - self.drag_offset_x
        target_origin_y = raw_y - self.drag_offset_y
        
        # 3. FIX: Snap to Transformer Grid
        snapped_x = self.api.transformer.snap_to_grid(target_origin_x)
        snapped_y = self.api.transformer.snap_to_grid(target_origin_y)
        
        # 4. Update
        self.ghost_item.x = snapped_x
        self.ghost_item.y = snapped_y
        
        if self.selected_item:
            self.selected_item.setPos(snapped_x, snapped_y)

    def on_mouse_release(self, event):
        if self.ghost_item:
            cmd = self.commit()
            if cmd:
                self.api.context.undo_stack.push(cmd)
            self.ghost_item = None
            self.selected_item = None

    def commit(self):
        if self._target and self.ghost_item:
            if self._target.x == self.ghost_item.x and self._target.y == self.ghost_item.y:
                return None
            return MoveCommand(self._target, self.ghost_item.x, self.ghost_item.y)
        return None