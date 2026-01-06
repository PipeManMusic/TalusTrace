import yaml
from pathlib import Path
from talustrace.backend.models import Harness

class ProjectContext:
    def __init__(self, harness: Harness = None):
        self.harness = harness or Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False

    def load(self, path: Path):
        """Loads a harness from a YAML file."""
        path = Path(path)
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        self.harness = Harness.model_validate(data)
        self.current_file = path
        self.dirty = False

    def save_as(self, path: Path):
        """Saves the current harness to a YAML file."""
        path = Path(path)
        with open(path, 'w') as f:
            data = self.harness.model_dump(mode='json')
            yaml.dump(data, f, sort_keys=False)
        self.current_file = path
        self.dirty = False
