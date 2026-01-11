# REMOVED top-level import to fix circular dependency
# from api.manager import APIManager 

class SelectionManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SelectionManager, cls).__new__(cls)
            cls._instance.selected_models = []
        return cls._instance

    @property
    def current_selection_ids(self):
        return [item.id for item in self.selected_models if hasattr(item, 'id')]

    def set_selection(self, models):
        """Updates the selection and notifies the API."""
        self.selected_models = models
        self._notify()

    def clear_selection(self):
        self.selected_models = []
        self._notify()

    def _notify(self):
        """Dispatches the selection_changed event safely."""
        # LAZY IMPORT: Breaks the cycle with api/manager.py
        from api.manager import APIManager
        
        # Guard against early calls before API is ready
        try:
            api = APIManager.get_instance()
            api.dispatch("selection_changed", {"selection": self.selected_models})
        except Exception:
            # If API isn't ready, we just skip notification (common during shutdown/startup)
            pass
