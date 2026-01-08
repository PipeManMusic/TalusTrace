from api.manager import APIManager

class SelectionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_selection_ids = set()
            cls._instance.selected_models = [] # Keep track of actual objects
        return cls._instance

    def set_selection(self, items):
        """
        Updates selection and notifies the system.
        items: List of Device/Wire objects (Logic Models, not UI Items)
        """
        self.selected_models = items
        self.current_selection_ids = set(getattr(i, 'id', i) for i in items)
        
        # Notify the App (Property Panel listens to this)
        APIManager.get_instance().dispatch("selection_changed", {
            "selection": self.selected_models
        })
        
        print(f">> Selection Updated: {len(items)} items")