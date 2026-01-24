"""
Selection module for Talus Trace.
Manages selection state and listener notification for models.
"""

# REMOVED top-level import to fix circular dependency
# from api.manager import APIManager 


class SelectionManager:
    """
    Singleton manager for model selection and listener notification.
    """
    _instance = None

    def __new__(cls):
        """
        Create or return the singleton instance of SelectionManager.
        """
        if cls._instance is None:
            cls._instance = super(SelectionManager, cls).__new__(cls)
            cls._instance.selected_models = []
            cls._instance._listeners = []
        return cls._instance

    def select(self, model):
        """Select a single model and notify listeners."""
        self.selected_models = [model]
        self._notify()

    def add_listener(self, callback):
        """Register a callback to be called on selection change."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback):
        """
        Remove a registered selection change listener.
        Args:
            callback (callable): Listener to remove.
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    @property
    def current_selection_ids(self):
        """
        Get the set of IDs for currently selected models.
        Returns:
            set: Set of selected model IDs.
        """
        return set(item.id for item in self.selected_models if hasattr(item, 'id'))


    def set_selection(self, models, on_complete=None, restore_previous=True):
        """
        Updates the selection and notifies the API.
        If on_complete is provided, runs it, then restores previous selection if requested.
        """
        prev_selection = self.selected_models[:]
        self.selected_models = models
        self._notify()
        if on_complete:
            def _after():
                """
                Restore previous selection and notify listeners after completion callback.
                """
                if restore_previous:
                    self.selected_models = prev_selection
                    self._notify()
            on_complete(_after)
        # If no on_complete, nothing else to do

    def clear_selection(self):
        """
        Clear all selected models and notify listeners.
        """
        self.selected_models = []
        self._notify()

    def _notify(self):
        """Dispatches the selection_changed event safely and notifies listeners."""
        # LAZY IMPORT: Breaks the cycle with api/manager.py
        for callback in self._listeners:
            try:
                callback(self.selected_models)
            except Exception as e:
                # ...removed debug print...
                pass
        from api.manager import APIManager
        
        # Guard against early calls before API is ready
        try:
            api = APIManager.get_instance()
            api.dispatch("selection_changed", {"selection": self.selected_models})
        except Exception:
            # If API isn't ready, we just skip notification (common during shutdown/startup)
            pass
