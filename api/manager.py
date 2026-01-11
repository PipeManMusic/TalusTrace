from infra.context import ProjectContext
from api.tool_manager import ToolManager
from core.library_manager import LibraryManager
from ui.input_system import InputSystem
from ui.coordinates import CoordinateTransformer # <--- NEW

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
        
        self.context = ProjectContext()
        self.library = LibraryManager()
        self.transformer = CoordinateTransformer() # <--- SINGLE SOURCE OF TRUTH
        self.tool_manager = ToolManager()
        
        # Register Tools
        from tools.select_tool import SelectTool
        from tools.wire_tool import WireTool
        from tools.placement_tool import PlacementTool
        # Register MoveTool (Lazy loaded or explicit)
        from tools.move_tool import MoveTool 
        
        self.tool_manager.register_tool("select", SelectTool())
        self.tool_manager.register_tool("wire", WireTool())
        self.tool_manager.register_tool("placement", PlacementTool())
        self.tool_manager.register_tool("move", MoveTool())
        
        self.input_system = InputSystem()
        self._subscribers = {}
        self.main_window = None

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def dispatch(self, event_type, data=None):
        if data is None: data = {}
        if event_type in self._subscribers:
            for cb in list(self._subscribers[event_type]):
                try:
                    cb(data)
                except RuntimeError:
                    pass 
                except Exception as e:
                    print(f"Error dispatching '{event_type}': {e}")