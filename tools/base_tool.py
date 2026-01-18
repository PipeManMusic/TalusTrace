class BaseTool:
    __guide__ = "Base tool for all interaction tools. Implements start/stop and event hooks."
    def __init__(self):
        pass
    def start(self):
        pass
    def stop(self):
        pass
    def on_mouse_move(self, event):
        """event: CanvasEvent"""
        pass
    def on_mouse_press(self, event):
        """event: CanvasEvent"""
        pass

# Backward compatibility for legacy imports
Tool = BaseTool
