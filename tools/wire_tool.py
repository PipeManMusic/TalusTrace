from tools.base_tool import Tool
# REMOVED: from api.manager import APIManager (Circular Dependency)

class WireTool(Tool):
    def __init__(self):
        super().__init__()
        self.active_wire = None

    def start(self):
        print(">> WireTool Activated")
        # LAZY LOAD: Safe because Manager is fully initialized by now
        from api.manager import APIManager
        
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
        
        # LAZY LOAD
        from api.manager import APIManager
        api = APIManager.get_instance()
        
        if hasattr(api, 'main_window'):
            from PySide6.QtCore import Qt
            api.main_window.canvas.setCursor(Qt.ArrowCursor)
