import yaml
from pathlib import Path
from core.models import Harness

class ProjectContext:
    def __init__(self, harness=None):
        self.harness = harness if harness is not None else Harness()
        self.dirty = False
        self.current_file = None
        # Add command_manager for infra command execution
        from infra.commands import CommandManager
        self.command_manager = CommandManager()

    def save_as(self, file_path: Path):
        with open(file_path, 'w') as f:
            yaml.safe_dump(self.harness.to_dict(), f, sort_keys=False)
        self.dirty = False
        self.current_file = file_path

    def load(self, file_path: Path):
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        self.harness = Harness.from_dict(data)
        self.dirty = False
        self.current_file = file_path
