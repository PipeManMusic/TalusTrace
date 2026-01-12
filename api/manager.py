from infra.context import Context
from infra.settings import SystemSettings
from core.library_manager import LibraryManager
from ui.input_system import InputSystem

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
            
        # --- PHASE 1: CORE FOUNDATION ---
        self.settings = SystemSettings()  # Physics (Grid/Units)
        self.context = Context()          # Session Data
        self.library = LibraryManager()   # Part Database
        
        # --- PHASE 2: SERVICE LAYER ---
        self.input_system = InputSystem()
        self.tool_manager = None
        self.main_window = None # Set by UI later
        
        # Initialize Tools (Lazy import to avoid circles)
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
        self.context.observer.subscribe(event_type, callback)

    def dispatch(self, event_type, data=None):
        if data is None: data = {}
        self.context.observer.dispatch(event_type, data)