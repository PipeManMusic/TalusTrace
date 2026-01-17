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
        print(f"[ToolManager] set_tool called: name={name}, args={args}, kwargs={kwargs}")
        if name not in self._tools:
            print(f">> Error: Tool '{name}' not found.")
            return

        if self.active_tool == self._tools[name]:
            print(f"[ToolManager] Tool '{name}' already active. Forcing reactivation with new args.")
            # Always call start() with new args to update tool state
            print(f"[ToolManager] Calling start on tool '{name}' with args={args}, kwargs={kwargs}")
            self.active_tool.start(*args, **kwargs)
            return

        # Deactivate existing tool before switching
        if self.active_tool:
            print(f"[ToolManager] Deactivating current tool: {self.active_tool}")
            self.active_tool.deactivate()

        self.active_tool = self._tools[name]
        print(f">> Tool Changed: {name}")
        # Pass args/kwargs to start() for event context (MAP-compliant)
        print(f"[ToolManager] Calling start on tool '{name}' with args={args}, kwargs={kwargs}")
        self.active_tool.start(*args, **kwargs)

    def execute_action(self, action_id, context=None):
        """
        Executes an action via the global ActionRegistry.
        """
        registry.execute(action_id, context)