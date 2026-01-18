from api.actions import registry

class ToolManager:
    def __init__(self):
        self._tools = {}
        self.active_tool = None

    def register_tool(self, name, tool):
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
        if self.active_tool:
            # ...removed debug print...
            self.active_tool.deactivate()

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