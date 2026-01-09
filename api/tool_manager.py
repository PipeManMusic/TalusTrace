class ToolManager:
    def __init__(self):
        self._tools = {}
        self.active_tool = None

    def register_tool(self, name, tool):
        self._tools[name] = tool

    def get_tool(self, name):
        """Retrieves a registered tool by its name."""
        return self._tools.get(name)

    def set_tool(self, name):
        """Sets active tool and handles transition cleanup internally."""
        if name not in self._tools:
            print(f">> Error: Tool '{name}' not found.")
            return

        if self.active_tool == self._tools[name]:
            return

        # Deactivate existing tool before switching
        if self.active_tool:
            self.active_tool.deactivate()

        self.active_tool = self._tools[name]
        print(f">> Tool Changed: {name}")
        
        # Initialize the new state
        self.active_tool.start()