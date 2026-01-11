from tools.base_tool import Tool
from api.manager import APIManager

class WireTool(Tool):
    def __init__(self):
        super().__init__()
        self.active_wire = None

    def start(self):
        print(">> WireTool Activated")
        api = APIManager.get_instance()
        if hasattr(api, 'main_window'):
            from PySide6.QtCore import Qt
            api.main_window.canvas.setCursor(Qt.CrossCursor)

    def on_mouse_press(self, event):
        print(f"WireTool Click at {event.pos_mm}")

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass

    def deactivate(self):
        print(">> WireTool Deactivated")
        self.active_wire = None
        api = APIManager.get_instance()
        if hasattr(api, 'main_window'):
            from PySide6.QtCore import Qt
            api.main_window.canvas.setCursor(Qt.ArrowCursor)
