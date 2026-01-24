"""
Base tool class for all interaction tools in Talus Trace.
Implements start/stop and event hooks for tool behaviors.
"""
from api.manager import APIManager
class BaseTool:
    """
    Base tool for all interaction tools. Implements start/stop and event hooks.
    """
    __guide__ = "Base tool for all interaction tools. Implements start/stop and event hooks."
    def __init__(self):
        """
        Initialize the BaseTool.
        """
        self._api_instance = None  # For testing injection

    @property
    def api(self):
        """
        Get the APIManager instance for the tool.
        """
        if self._api_instance:
            return self._api_instance
        return APIManager.get_instance()

    @api.setter
    def api(self, value):
        """
        Set a custom APIManager instance (for testing).
        """
        self._api_instance = value

    def deactivate(self):
        """
        Called when the tool is deactivated.
        """
        pass

    def cancel(self):
        """
        Default cancel behavior.
        """
        pass

    # Stub event handlers to prevent AttributeErrors
    def on_mouse_press(self, event):
        """
        Handle mouse press event.
        Args:
            event: Mouse event.
        """
        pass

    def on_mouse_move(self, event):
        """
        Handle mouse move event.
        Args:
            event: Mouse event.
        """
        pass

    def on_mouse_release(self, event):
        """
        Handle mouse release event.
        Args:
            event: Mouse event.
        """
        pass

    def on_key_press(self, event):
        """
        Handle key press event.
        Args:
            event: Key event.
        """
        pass
    def stop(self):
        """
        Stop the tool.
        """
        pass

# Backward compatibility for legacy imports
Tool = BaseTool
