"""
Selection Manager Design:
-------------------------
The SelectionManager is responsible for tracking and managing the current selection state within the application. It provides APIs to select, deselect, and query selected items, and emits signals when the selection changes. This enables decoupled UI components and tools to react to selection changes without direct dependencies. The design supports multi-selection, selection filtering, and integration with undo/redo and event systems. All selection logic is centralized here to ensure consistency and maintainability.
"""
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
        import traceback
        print(f"[SELECTION][select] Selecting model: {repr(model)} id={getattr(model, 'id', None)} objid={id(model)}")
        self.selected_models = [model]
        print(f"[SELECTION][select] selected_models: {[getattr(m, 'id', None) for m in self.selected_models]}")
        print(f"[SELECTION][select] Call stack:")
        traceback.print_stack(limit=6)
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
        import traceback
        prev_selection = self.selected_models[:]
        print(f"[SELECTION][set_selection] Setting selection: {[getattr(m, 'id', None) for m in models]}")
        print(f"[SELECTION][set_selection] Previous selection: {[getattr(m, 'id', None) for m in prev_selection]}")
        self.selected_models = models
        print(f"[SELECTION][set_selection] selected_models: {[getattr(m, 'id', None) for m in self.selected_models]}")
        print(f"[SELECTION][set_selection] Call stack:")
        traceback.print_stack(limit=6)
        self._notify()
        if on_complete:
            def _after():
                """
                Restore previous selection and notify listeners after completion callback.
                """
                if restore_previous:
                    self.selected_models = prev_selection
                    print(f"[SELECTION][set_selection][after] Restoring previous selection: {[getattr(m, 'id', None) for m in prev_selection]}")
                    self._notify()
            on_complete(_after)
        # If no on_complete, nothing else to do

    def clear_selection(self):
        """
        Clear all selected models and notify listeners.
        """
        import traceback
        print(f"[SELECTION][clear_selection] Clearing selection. Previous: {[getattr(m, 'id', None) for m in self.selected_models]}")
        self.selected_models = []
        print(f"[SELECTION][clear_selection] selected_models: {self.selected_models}")
        print(f"[SELECTION][clear_selection] Call stack:")
        traceback.print_stack(limit=6)
        self._notify()

    def _notify(self):
        """Dispatches the selection_changed event safely and notifies listeners."""
        import traceback
        print(f"[SELECTION][_notify] Notifying listeners. selected_models: {[getattr(m, 'id', None) for m in self.selected_models]}")
        for callback in self._listeners:
            try:
                callback(self.selected_models)
            except Exception as e:
                print(f"[SELECTION][_notify] Listener exception: {e}")
                traceback.print_exc()
        # LAZY IMPORT: Breaks the cycle with api/manager.py
        from api.manager import APIManager
        # Guard against early calls before API is ready
        try:
            api = APIManager.get_instance()
            print(f"[SELECTION][_notify] Dispatching 'selection_changed' via APIManager. selected_models: {[getattr(m, 'id', None) for m in self.selected_models]}")
            api.dispatch("selection_changed", {"selection": self.selected_models})
        except Exception as e:
            print(f"[SELECTION][_notify] Exception during API dispatch: {e}")
            traceback.print_exc()
            # If API isn't ready, we just skip notification (common during shutdown/startup)
            pass
