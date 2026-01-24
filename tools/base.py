"""
Base tool class for interaction tools in Talus Trace.
Defines the interface for tool activation, deactivation, and event hooks.
"""
class BaseTool:
    """
    Base class for all interaction tools. Implements start/stop and event hooks.
    """
    __guide__ = "BaseTool: Base class for all interaction tools. Implements start/stop and event hooks."
    def activate(self):
        """
        Activate the tool and prepare for interaction.
        """
        pass

    def deactivate(self):
        """
        Deactivate the tool and perform cleanup.
        """
        pass

    def on_mouse_press(self, event):
        """
        Handle mouse press event.
        Args:
            event: Mouse event.
        """
        pass

    def on_mouse_double_click(self, event):
        """
        Handle mouse double click event.
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