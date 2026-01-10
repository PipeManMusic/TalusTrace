from infra.undo_stack import BaseCommand
from api.manager import APIManager
from core.device import Device

class MoveCommand(BaseCommand):
    def __init__(self, target, new_x, new_y):
        super().__init__("MoveCommand")
        self.target = target
        self.new_x = new_x
        self.new_y = new_y
        self.old_x = target.x
        self.old_y = target.y

    def execute(self, target=None):
        tgt = target if target is not None else self.target
        tgt.x = self.new_x
        tgt.y = self.new_y

    def undo(self):
        self.target.x = self.old_x
        self.target.y = self.old_y

class MoveTool:
    def __init__(self):
        self.ghost_item = None
        self._target = None
        self.selected_item = None
        self.elbow_index = None
        self.elbow_drag = False

    def start(self, target=None, selected_item=None):
        """
        Starts a move operation. 
        Args optional to support ToolManager activation without immediate target.
        """
        if target:
            self._target = target
            self.ghost_item = type(target)(**target.model_dump())
            self.selected_item = selected_item

    def activate(self): pass

    def deactivate(self):
        self.ghost_item = None
        self.selected_item = None

    def on_mouse_press(self, event):
        self.elbow_index = None
        self.elbow_drag = False
        
        if hasattr(event, 'scene_item') and event.scene_item:
            item = event.scene_item
            
            # 1. Elbow Logic (BundleItem)
            if hasattr(item, 'path_nodes'):
                pos = event.pos_mm
                for idx, node in enumerate(item.path_nodes):
                    dist = ((pos.x() - node[0]) ** 2 + (pos.y() - node[1]) ** 2) ** 0.5
                    if dist < 5.0:
                        self.elbow_index = idx
                        self.selected_item = item
                        self.elbow_drag = True
                        break
            
            # 2. Device Logic (DeviceItem)
            # REFACTOR: Check for .model instead of .device
            elif hasattr(item, 'model') and isinstance(item.model, Device):
                self.start(item.model, item)

    def on_mouse_move(self, event):
        if not hasattr(event, 'pos_mm'): return
        
        grid_size = 25.0
        x = round(event.pos_mm.x() / grid_size) * grid_size
        y = round(event.pos_mm.y() / grid_size) * grid_size
        
        if self.elbow_drag and self.selected_item:
            self.selected_item.path_nodes[self.elbow_index] = (x, y)
            self.selected_item.update()
            
        elif self.ghost_item:
            dx = x - self.ghost_item.x
            dy = y - self.ghost_item.y
            self.update(dx, dy)

    def update(self, dx, dy):
        if self.ghost_item:
            self.ghost_item.x += dx
            self.ghost_item.y += dy
            
        if self.selected_item:
            self.selected_item.setPos(self.ghost_item.x, self.ghost_item.y)
            
            # REFACTOR: Sync model using .model
            if hasattr(self.selected_item, 'model'):
                self.selected_item.model.x = self.ghost_item.x
                self.selected_item.model.y = self.ghost_item.y

    def on_mouse_release(self, event):
        if self.elbow_drag:
            self.elbow_drag = False
            return

        if self.ghost_item:
            cmd = self.commit()
            if cmd:
                APIManager.get_instance().context.undo_stack.push(cmd)
            self.ghost_item = None
            self.selected_item = None

    def commit(self):
        if self._target and self.ghost_item:
            return MoveCommand(self._target, self.ghost_item.x, self.ghost_item.y)
        return None
