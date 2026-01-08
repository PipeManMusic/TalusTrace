from tools.base import BaseTool

class ToolManager:
    def __init__(self):
        self._active_tool = None
        self._tools = {}

    def register_tool(self, name: str, tool_instance: BaseTool):
        self._tools[name] = tool_instance

    def set_tool(self, name: str):
        if self._active_tool:
            self._active_tool.deactivate()
        
        if name in self._tools:
            self._active_tool = self._tools[name]
            self._active_tool.activate()
            print(f">> Tool Changed: {name}")
        else:
            print(f">> Error: Tool '{name}' not registered.")

    @property
    def active_tool(self):
        return self._active_tool