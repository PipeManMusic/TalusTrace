from PySide6.QtCore import Qt
from tools.base_tool import Tool
from core.selection import SelectionManager

class SelectTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas

    @property
    def api(self):
        """Lazy load API to avoid circular imports."""
        from api.manager import APIManager
        return APIManager.get_instance()

    def start(self):
        if not self.canvas:
            if hasattr(self.api, 'main_window'):
                self.canvas = self.api.main_window.canvas
        if self.canvas:
            self.canvas.viewport().setCursor(Qt.ArrowCursor)

    def on_mouse_press(self, event):
        modifiers = event.original_event.modifiers()
        is_multi = (modifiers & Qt.ControlModifier) or (modifiers & Qt.ShiftModifier)
        item = event.scene_item
        
        # 1. Update Visual Selection (Qt)
        if item:
            if not is_multi:
                for sel in event.scene.selectedItems():
                    if sel != item: sel.setSelected(False)
            item.setSelected(not item.isSelected() if is_multi else True)
        else:
            if not is_multi:
                event.scene.clearSelection()

        # 2. Sync to Core
        self._update_core_selection(event.scene)

    def _update_core_selection(self, scene):
        selected_models = []
        for item in scene.selectedItems():
            if hasattr(item, 'model'):
                selected_models.append(item.model)
        
        SelectionManager().set_selection(selected_models)

    # --- KEYBOARD HANDLERS ---
    def on_key_press(self, event):
        key = event.key()
        
        # 1. DELETE
        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            selection = SelectionManager().selected_models
            if not selection: return

            from api.commands.edit import DeleteItemsCommand
            
            # Sort selection into Devices vs Wires
            dev_ids = []
            wire_ids = []
            
            for item in selection:
                # Heuristic: Devices have 'meta' dict, Wires don't (usually)
                if hasattr(item, 'meta'):
                    dev_ids.append(item.id)
                else:
                    # Fallback for wires (which might not have IDs yet, but let's try)
                    if hasattr(item, 'id'):
                        wire_ids.append(item.id)

            if dev_ids or wire_ids:
                cmd = DeleteItemsCommand(dev_ids, wire_ids)
                self.api.context.undo_stack.push(cmd)
            
            return # Consume event

        # 2. ROTATE (R)
        elif key == Qt.Key_R:
            selection = SelectionManager().selected_models
            if not selection: return

            from api.commands.edit import RotateItemsCommand
            
            # Rotate 90 degrees Clockwise
            cmd = RotateItemsCommand(selection, 90)
            self.api.context.undo_stack.push(cmd)
            return

    def on_mouse_move(self, event): pass
    def on_mouse_release(self, event): pass
    def deactivate(self): pass