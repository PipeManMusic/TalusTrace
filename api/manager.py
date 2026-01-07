from infra.context import ProjectContext


class APIManager:
    _instance = None

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.context = ProjectContext()
            self._observers = []
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, callback):
        """Register an observer callback for state change notifications."""
        if callback not in self._observers:
            self._observers.append(callback)

    def unsubscribe(self, callback):
        """Remove an observer callback."""
        if callback in self._observers:
            self._observers.remove(callback)

    def dispatch(self, event_type, payload):
        """Simulate a state update and notify observers."""
        # Here, you would update the core state as needed
        # For test, just notify observers with the payload
        event_data = payload.copy()
        event_data['event_type'] = event_type
        for observer in self._observers:
            observer(event_data)
