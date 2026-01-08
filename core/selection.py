
class SelectionManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_selection_ids = set()
        return cls._instance

    def set_selection(self, items):
        # Accepts a list of devices, sets their ids as selected
        self.current_selection_ids = set(getattr(i, 'id', i) for i in items)
