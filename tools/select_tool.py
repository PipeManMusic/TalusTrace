from tools.base_tool import Tool
from api.manager import APIManager

class SelectTool(Tool):
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas

    def start(self):
        """Initializes the selection state when activated."""
        if not self.canvas:
            api = APIManager.get_instance()
            if hasattr(api, 'main_window'):
                self.canvas = api.main_window.canvas

        print(">> Selection Mode Active")
        if self.canvas:
            self.canvas.viewport().setCursor(None) 

    def on_mouse_press(self, event):
        """Handles item selection logic using the CanvasEvent wrapper."""
        item = event.scene_item
        if item:
            item.setSelected(True)
            print(f">> Selected: {item}")
        else:
            event.scene.clearSelection()
            print(">> Selection Cleared")

    def on_mouse_move(self, event):
        """Stub for InputSystem compatibility."""
        pass

    def on_mouse_release(self, event):
        """Required stub to prevent AttributeError on mouse up."""
        pass

    def deactivate(self):
        """Standard cleanup for the selection tool."""
        print(">> Deactivating Selection Mode")

    def stop(self):
        self.deactivate()