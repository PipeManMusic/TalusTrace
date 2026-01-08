from infra.context import ProjectContext
from api.tool_manager import ToolManager

class APIManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.context = ProjectContext()
            
            # --- FIX: Initialize Tool Manager ---
            self.tool_manager = ToolManager()
            
            self.input_system = None
            self._observers = []
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, callback):
        if callback not in self._observers:
            self._observers.append(callback)

    def unsubscribe(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def dispatch(self, event_type, payload):
        event_data = payload.copy()
        event_data['event_type'] = event_type
        for observer in self._observers:
            observer(event_data)