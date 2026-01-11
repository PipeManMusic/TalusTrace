from infra.context import Context
from ui.input_system import InputSystem
from infra.settings import SystemSettings
# FIXED: Restore Library Manager
from core.library_manager import LibraryManager

class APIManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if APIManager._instance is not None:
            raise Exception("This class is a singleton!")
            
        # 1. Core Systems
        self.settings = SystemSettings() # Physics/Grid
        self.context = Context()         # Data/Session
        self.library = LibraryManager()  # Part Library <--- RESTORED
        self.input_system = InputSystem()
        
        # 2. Tool Manager & Registration
        # We import inside __init__ to avoid circular dependency loops
        from api.tool_manager import ToolManager
        from tools.select_tool import SelectTool
        from tools.wire_tool import WireTool
        from tools.placement_tool import PlacementTool
        from tools.move_tool import MoveTool
        
        self.tool_manager = ToolManager()
        self.tool_manager.register_tool("select", SelectTool())
        self.tool_manager.register_tool("wire", WireTool())
        self.tool_manager.register_tool("placement", PlacementTool())
        self.tool_manager.register_tool("move", MoveTool())

    def subscribe(self, event_type, callback):
        # Delegate to the Context's Observer
        self.context.observer.subscribe(event_type, callback)

    def dispatch(self, event_type, data=None):
        if data is None: data = {}
        self.context.observer.dispatch(event_type, data)