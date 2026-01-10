from api.manager import APIManager

class SelectionManager:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_selection_ids = set()
            cls._instance.selected_models = []
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

    def select(self, item):
        """
        Adds a single item to the selection.
        Safe wrapper that prevents duplicates and triggers updates.
        """
        if hasattr(item, 'id') and item.id in self.current_selection_ids:
            return
        
        # Append to existing and refresh
        self.set_selection(self.selected_models + [item])

    def deselect(self, item):
        """
        Removes a single item from the selection.
        """
        if hasattr(item, 'id') and item.id not in self.current_selection_ids:
            return
            
        # Filter out the item and refresh
        new_selection = [
            i for i in self.selected_models 
            if getattr(i, 'id', None) != item.id
        ]
        self.set_selection(new_selection)

    def clear_selection(self):
        """
        Standard method to reset the selection state.
        This resolves the AttributeError in edit_delete.
        """
        self.set_selection([])