from infra.context import ProjectContext

class APIManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton for testing isolation."""
        cls._instance = None

    def __init__(self):
        self.context = ProjectContext()
        self._observers = []
        
        # Initialize Subsystems
        try:
            from api.tool_manager import ToolManager
            self.tool_manager = ToolManager()
        except ImportError:
            self.tool_manager = None
            
        try:
            from ui.input_system import InputSystem
            self.input_system = InputSystem()
        except ImportError:
            self.input_system = None

    # RENAMED: observe -> subscribe (Matches Test Suite expectation)
    def subscribe(self, callback):
        """Register a callback to receive app-wide events."""
        if callback not in self._observers:
            self._observers.append(callback)


    def _dispatch(self, event_name, data=None):
        """Notify all observers of an event."""
        if data is None:
            data = {}
        # Standardize event packet
        if isinstance(data, dict):
            data['event'] = event_name
        for callback in self._observers:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in observer {callback}: {e}")

    @classmethod
    def dispatch(cls, event_name, data=None):
        """Class-level dispatch for test patching."""
        instance = cls.get_instance()
        instance._dispatch(event_name, data)