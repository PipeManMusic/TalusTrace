from PySide6.QtWidgets import QApplication
from api.actions import register_action
from api.manager import APIManager
from infra.undo_stack import BaseCommand

# --- Command Implementation ---
class UpdatePropertyCommand(BaseCommand):
    def __init__(self, target, field, new_value):
        super().__init__(f"Update {field}")
        self.target = target
        self.field = field
        self.new_value = new_value
        # Handle dictionary vs object attribute
        if isinstance(target, dict):
            self.old_value = target.get(field)
            self.is_dict = True
        else:
            self.old_value = getattr(target, field, None)
            self.is_dict = False

    def execute(self):
        if self.is_dict:
            self.target[self.field] = self.new_value
        else:
            setattr(self.target, self.field, self.new_value)
        self._refresh()

    def undo(self):
        if self.is_dict:
            self.target[self.field] = self.old_value
        else:
            setattr(self.target, self.field, self.old_value)
        self._refresh()

    def _refresh(self):
        # Notify system of change
        api = APIManager.get_instance()
        api.dispatch("model_changed", {"item": self.target})
        if hasattr(api, 'main_window') and api.main_window:
            api.main_window.canvas.scene.update()

# --- Action Registrations ---

@register_action("edit.undo")
def edit_undo(context):
    APIManager.get_instance().context.undo_stack.undo()

@register_action("edit.redo")
def edit_redo(context):
    APIManager.get_instance().context.undo_stack.redo()

@register_action("edit.delete")
def edit_delete(context):
    from core.selection import SelectionManager
    api = APIManager.get_instance()
    mgr = SelectionManager()
    
    ids = set(mgr.current_selection_ids)
    if not ids: return

    # Remove items (Logic should ideally be in a reversible Command)
    api.context.harness.devices = [d for d in api.context.harness.devices if d.id not in ids]
    api.context.harness.wires = [w for w in api.context.harness.wires if getattr(w, 'id', None) not in ids]
    
    mgr.clear_selection()
    
    api.dispatch("model_changed", {"action": "delete"})
    if hasattr(api, 'main_window'):
        api.main_window.canvas.load_harness(api.context.harness)

@register_action("edit.rotate_cw")
def edit_rotate_cw(context):
    _rotate_selection(90)

@register_action("edit.rotate_ccw")
def edit_rotate_ccw(context):
    _rotate_selection(-90)

def _rotate_selection(angle):
    from core.selection import SelectionManager
    api = APIManager.get_instance()
    mgr = SelectionManager()
    
    count = 0
    for item in mgr.selected_models:
        if hasattr(item, 'rotation'):
            item.rotation = (item.rotation + angle) % 360
            count += 1
            
    if count > 0:
        api.dispatch("model_changed", {"action": "rotate"})
        if hasattr(api, 'main_window'):
            api.main_window.canvas.scene.update()
            # Refresh property panel
            api.dispatch("selection_changed", {"selection": mgr.selected_models})

@register_action("edit.update_property")
def edit_update_property(context):
    pass
