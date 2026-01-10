from PySide6.QtCore import Qt
from tools.base_tool import Tool
# REMOVE: from api.manager import APIManager (Causes Crash)

class SelectTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas

    def start(self):
        """Initialize cursor and try to cache canvas reference."""
        # FIX: Import here to break the circular loop
        from api.manager import APIManager 
        
        if not self.canvas:
            api = APIManager.get_instance()
            if hasattr(api, 'main_window'):
                self.canvas = api.main_window.canvas
        
        if self.canvas:
            self.canvas.viewport().setCursor(Qt.ArrowCursor)

    def on_mouse_press(self, event):
        """
        Handles click selection with proper modifier support.
        """
        # 1. Check for Modifier Keys (Ctrl/Shift)
        modifiers = event.original_event.modifiers()
        is_multi_select = (modifiers & Qt.ControlModifier) or (modifiers & Qt.ShiftModifier)

        item = event.scene_item
        
        # 2. Clicking on an Item
        if item:
            # Explicitly clear others if NOT multi-select.
            if not is_multi_select:
                for selected in event.scene.selectedItems():
                    if selected != item:
                        selected.setSelected(False)
            
            # Toggle if multi-select, otherwise ensure selected
            if is_multi_select:
                item.setSelected(not item.isSelected())
            else:
                item.setSelected(True)
            
            print(f">> Selected: {item}")
                
        # 3. Clicking on Empty Space
        else:
            if not is_multi_select:
                event.scene.clearSelection()
                print(">> Selection Cleared")

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass

    def deactivate(self):
        pass