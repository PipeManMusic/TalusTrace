from infra.context import ProjectContext
from api.tool_manager import ToolManager
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
        
        self.context = ProjectContext()
        self.tool_manager = ToolManager()
        self.library = LibraryManager() # <--- NEW: Centralized Library
        
        self._subscribers = {}
        
        # Lazy load InputSystem
        from ui.input_system import InputSystem
        self.input_system = InputSystem()
        self.input_system.install()

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def dispatch(self, event_type, data):
        if event_type in self._subscribers:
            for cb in self._subscribers[event_type]:
                try:
                    cb(data)
                except Exception as e:
                    print(f"Error dispatching '{event_type}': {e}")
