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
        self._last_selection = [item for item in event.scene.selectedItems()]
        modifiers = event.original_event.modifiers()
        is_multi = (modifiers & Qt.ControlModifier) or (modifiers & Qt.ShiftModifier)
        item = event.scene_item

        from core.device import Device
        from ui.items.elbow_grip import ElbowGripItem
        from ui.items.segment_grip import SegmentGripItem
        # Tool handoff logic (unchanged)
        if item and hasattr(item, 'model') and isinstance(item.model, Device) and not is_multi:
            # Select the device via API so PropertyPanel updates
            self.api.select([item.model.id], tool_name="SelectTool")
            move_tool = self.api.tool_manager.get_tool('move')
            self.api.tool_manager.set_tool('move', target=item.model, selected_item=item, click_pos=event.pos_mm)
            move_tool.on_mouse_press(event)
            self._restore_selection_later(event.scene)
            return
        if isinstance(item, ElbowGripItem) and not is_multi:
            self.api.tool_manager.set_tool('elbow_move', item.wire_item, item.index, event)
            self._restore_selection_later(event.scene)
            return
        if isinstance(item, SegmentGripItem) and not is_multi:
            self.api.tool_manager.set_tool('segment_move', item.wire_item, item.start_idx, item.end_idx, event)
            self._restore_selection_later(event.scene)
            return

        # If no selectable item and not multi-select, clear selection
        if not item and not is_multi:
            self.api.clear_selection(tool_name="SelectTool")
            return

        # Only notify API of selection intent; do not set Qt selection directly
        self._update_core_selection(event.scene)
    def _restore_selection_later(self, scene):
        # Restore previous selection after tool completes
        from PySide6.QtCore import QTimer
        def restore():
            # Only restore if user hasn't cleared selection
            if hasattr(self, '_last_selection') and self._last_selection:
                # Deselect items not in last selection
                for sel in scene.selectedItems():
                    if sel not in self._last_selection:
                        try:
                            sel.setSelected(False)
                        except RuntimeError:
                            pass
                # Select items in last selection, skip deleted
                for item in self._last_selection:
                    try:
                        item.setSelected(True)
                    except RuntimeError:
                        pass
                # Sync to core
                self._update_core_selection(scene)
        QTimer.singleShot(0, restore)

        # Removed stray 'if item:' line causing NameError
        # 1. Update Visual Selection (Qt)
        # The logic related to 'item' has been removed to prevent NameError
        # If you need to update selection here, ensure correct context and indentation.
        # Example placeholder (commented out):
        # if not is_multi:
        #     for sel in scene.selectedItems():
        #         sel.setSelected(False)
        # else:
        #     scene.clearSelection()

        # 2. Sync to Core
        self._update_core_selection(scene)

    def _update_core_selection(self, scene):
        # Gather selected item IDs
        selected_ids = [item.model.id for item in scene.selectedItems() if hasattr(item, 'model') and hasattr(item.model, 'id')]
        tool_name = self.__class__.__name__
        # Send selection request to API
        self.api.select(selected_ids, tool_name)

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

    def on_mouse_move(self, event):
        # If MoveTool is active, forward event
        if self.api.tool_manager.active_tool == self.api.tool_manager.get_tool('move'):
            self.api.tool_manager.active_tool.on_mouse_move(event)
            return
        # Otherwise, do nothing (selection tool doesn't handle drag)
        pass
    def on_mouse_release(self, event):
        # If MoveTool is active, forward event
        if self.api.tool_manager.active_tool == self.api.tool_manager.get_tool('move'):
            self.api.tool_manager.active_tool.on_mouse_release(event)
            # After move, switch back to select tool
            self.api.tool_manager.set_tool('select')
            return
        pass
    def deactivate(self): pass