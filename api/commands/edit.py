from api.actions import register_action
from api.manager import APIManager
from infra.undo_stack import BaseCommand
from core.selection import SelectionManager

# --- Command Classes ---

class UpdatePropertyCommand(BaseCommand):
    def __init__(self, target, field, new_value):
        super().__init__(f"Update {field}")
        self.target = target
        self.field = field
        self.new_value = new_value
        self.is_dict = isinstance(target, dict)
        self.old_value = target.get(field) if self.is_dict else getattr(target, field, None)
        self.api = APIManager.get_instance()

    def execute(self):
        if self.is_dict: self.target[self.field] = self.new_value
        else: setattr(self.target, self.field, self.new_value)
        self.api.dispatch("model_changed", {"action": "update", "item": self.target})

    def undo(self):
        if self.is_dict: self.target[self.field] = self.old_value
        else: setattr(self.target, self.field, self.old_value)
        self.api.dispatch("model_changed", {"action": "update", "item": self.target})

class DeleteItemsCommand(BaseCommand):
    def __init__(self, device_ids, wire_ids):
        super().__init__("Delete Items")
        self.dev_ids = device_ids
        self.wire_ids = wire_ids
        self.api = APIManager.get_instance()
        # Capture state for undo
        self.deleted_devices = []
        self.deleted_wires = []

    def execute(self):
        harness = self.api.context.harness
        # Save for undo
        self.deleted_devices = [d for d in harness.devices if d.id in self.dev_ids]
        self.deleted_wires = [w for w in harness.wires if getattr(w, 'id', None) in self.wire_ids]
        
        # Mutate
        harness.devices = [d for d in harness.devices if d.id not in self.dev_ids]
        harness.wires = [w for w in harness.wires if getattr(w, 'id', None) not in self.wire_ids]
        
        SelectionManager().clear_selection()
        self.api.dispatch("model_changed", {"action": "delete"})

    def undo(self):
        harness = self.api.context.harness
        harness.devices.extend(self.deleted_devices)
        harness.wires.extend(self.deleted_wires)
        self.api.dispatch("model_changed", {"action": "restore"})

class RotateItemsCommand(BaseCommand):
    def __init__(self, items, angle):
        super().__init__("Rotate Items")
        self.items = items
        self.angle = angle
        self.api = APIManager.get_instance()

    def execute(self):
        for item in self.items:
            if hasattr(item, 'rotation'):
                item.rotation = (item.rotation + self.angle) % 360
        self.api.dispatch("model_changed", {"action": "rotate"})

    def undo(self):
        for item in self.items:
            if hasattr(item, 'rotation'):
                item.rotation = (item.rotation - self.angle) % 360
        self.api.dispatch("model_changed", {"action": "rotate"})

# --- Action Registrations ---

@register_action("edit.undo")
def edit_undo(context):
    APIManager.get_instance().context.undo_stack.undo()

@register_action("edit.redo")
def edit_redo(context):
    APIManager.get_instance().context.undo_stack.redo()

@register_action("edit.delete")
def edit_delete(context):
    mgr = SelectionManager()
    if not mgr.current_selection_ids: return
    
    # Identify what to delete
    dev_ids = []
    wire_ids = []
    
    for item in mgr.selected_models:
        if hasattr(item, 'meta'): # Heuristic for Device
            dev_ids.append(item.id)
        elif hasattr(item, 'id'): # Heuristic for Wire
            wire_ids.append(item.id)
    
    cmd = DeleteItemsCommand(dev_ids, wire_ids)
    APIManager.get_instance().context.undo_stack.push(cmd)

@register_action("edit.rotate_cw")
def edit_rotate_cw(context):
    mgr = SelectionManager()
    if not mgr.selected_models: return
    cmd = RotateItemsCommand(mgr.selected_models, 90)
    APIManager.get_instance().context.undo_stack.push(cmd)

@register_action("edit.rotate_ccw")
def edit_rotate_ccw(context):
    mgr = SelectionManager()
    if not mgr.selected_models: return
    cmd = RotateItemsCommand(mgr.selected_models, -90)
    APIManager.get_instance().context.undo_stack.push(cmd)

@register_action("edit.update_property")
def edit_update_property(context):
    pass # Invoked programmatically by PropertyPanel
