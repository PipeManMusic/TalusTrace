from api.manager import APIManager
class BaseTool:
    __guide__ = "Base tool for all interaction tools. Implements start/stop and event hooks."
    def __init__(self):
        self._api_instance = None  # For testing injection


    @property
    def api(self):
        if self._api_instance:
            return self._api_instance
        return APIManager.get_instance()

    @api.setter
    def api(self, value):
        self._api_instance = value


    def deactivate(self):
        """Called when the tool is deactivated."""
        pass

    def cancel(self):
        """Default cancel behavior."""
        pass

    # Stub event handlers to prevent AttributeErrors
    def on_mouse_press(self, event):
        pass

    def on_mouse_move(self, event):
        pass

    def on_mouse_release(self, event):
        pass

    def on_key_press(self, event):
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
