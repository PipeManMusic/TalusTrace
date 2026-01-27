
"""
ToolManager for registering, activating, and managing tools in Talus Trace.
Handles tool lifecycle, transitions, and integration with the global ActionRegistry.
"""
from api.actions import registry

class ToolManager:
    """
    Manages registration, activation, and lifecycle of tools in the application.
    Provides methods to register, retrieve, and switch tools, and integrates with the ActionRegistry for action execution.
    """
    def __init__(self):
        """
        Initialize the ToolManager with an empty tool registry and no active tool.
        """
        self._tools = {}
        self.active_tool = None

    def register_tool(self, name, tool):
        """
        Register a tool with the given name and set its 'api' property to the current APIManager instance.
        Args:
            name (str): The name of the tool.
            tool: The tool instance to register.
        """
        from api.manager import APIManager
        api_instance = APIManager.get_instance()
        # Only set api if it is not a read-only property
        if not (hasattr(type(tool), 'api') and isinstance(getattr(type(tool), 'api'), property) and not getattr(type(tool), 'api').fset):
            setattr(tool, 'api', api_instance)
        self._tools[name] = tool

    def get_tool(self, name):
        """Retrieves a registered tool by its name."""
        return self._tools.get(name)

    def set_tool(self, name, *args, **kwargs):
        """Sets active tool and handles transition cleanup internally. Passes args/kwargs to start()."""
        # ...removed debug print...
        if name not in self._tools:
            # ...removed debug print...
            return

        if self.active_tool == self._tools[name]:
            # ...removed debug print...
            # Always call start() with new args to update tool state
            # ...removed debug print...
            self.active_tool.start(*args, **kwargs)
            return

        # Deactivate existing tool before switching
        """
        ToolManager for registering, activating, and managing tools in Talus Trace.
        Handles tool lifecycle, transitions, and integration with the global ActionRegistry.
        """

        from api.actions import registry
        self.active_tool = self._tools[name]
        # ...removed debug print...
        # Pass args/kwargs to start() for event context (MAP-compliant)
        # ...removed debug print...
        self.active_tool.start(*args, **kwargs)

    def execute_action(self, action_id, context=None):
        """
        Executes an action via the global ActionRegistry.
        """
        registry.execute(action_id, context)