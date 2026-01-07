import yaml
from pathlib import Path
from core.models import Harness

class ProjectContext:
    def __init__(self):
        self.harness = Harness()
        self.dirty = False
        self.current_file = None

    def save_as(self, file_path: Path):
        with open(file_path, 'w') as f:
            yaml.dump(self.harness.to_dict(), f, sort_keys=False)
        self.dirty = False
        self.current_file = file_path

    def load(self, file_path: Path):
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        self.harness = Harness.from_dict(data)
        self.dirty = False
        self.current_file = file_path
