import yaml
from pathlib import Path
# FIX: Import directly from core
from core.harness import Harness

class ProjectContext:
    def __init__(self, harness: Harness = None):
        self.harness = harness or Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False
        from infra.undo_stack import UndoStack
        self.undo_stack = UndoStack()


    @property
    def is_dirty(self):
        return self.dirty

    @is_dirty.setter
    def is_dirty(self, value):
        self.dirty = value

    def new_project(self):
        """Resets the context to a new harness and clears undo stack."""
        self.harness = Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False
        self.undo_stack.clear()

    def mark_dirty(self):
        self.dirty = True

    def mark_clean(self):
        self.dirty = False

    def load(self, path: Path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Harness file not found: {path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.harness = Harness.model_validate(data)
        self.current_file = path
        self.dirty = False

    def save_as(self, path: Path):
        """
        PH6-2.1: Uses safe_dump + model_dump(mode='json') for clean YAML.
        """
        path = Path(path)
        
        self.harness.increment_revision()
        
        # Converts all Models -> Dicts, Lists -> Lists, Enums -> Strings
        data = self.harness.model_dump(mode='json')
        
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
            
        self.current_file = path
        self.dirty = False