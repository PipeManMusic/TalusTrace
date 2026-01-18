import yaml
from pathlib import Path
from core.harness import Harness
from infra.observer import Observer 


class Context:
    def __init__(self, harness: Harness = None):
        self.harness = harness or Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False
        # Event Bus
        self.observer = Observer()
        # Undo Stack
        from infra.undo_stack import UndoStack
        self.undo_stack = UndoStack()

    def mark_clean(self):
        self.dirty = False

    @property
    def is_dirty(self):
        return self.dirty

    @is_dirty.setter
    def is_dirty(self, value):
        self.dirty = value

    def new_project(self):
        self.harness = Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True
        self.undo_stack.clear()
        self.observer.dispatch("model_changed", {"action": "new_project"})

    def load(self, path: Path):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Harness file not found: {path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.harness = Harness.model_validate(data)
        self.current_file = path
        self.dirty = False
        self.observer.dispatch("model_changed", {"action": "load"})

    def save_as(self, path: Path):
        path = Path(path)
        self.harness.increment_revision()
        data = self.harness.model_dump(mode='json')
        
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
            
        self.current_file = path
        self.dirty = False

# Backward compatibility for legacy imports
ProjectContext = Context