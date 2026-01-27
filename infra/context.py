"""
Context management for Talus Trace application.
Provides project/session state, undo/redo, autosave, and backup logic.
"""

import yaml
from pathlib import Path
from core.harness import Harness
from infra.observer import Observer
from infra.undo_stack import UndoStack


class Context:
    """
    Application context for managing project/session state, undo/redo, autosave, and backups.
    """
    AUTOSAVE_FILENAME = ".autosave.yaml"

    def replay_action_log(self, action_log, registry=None):
        """
        Replay a list of action log entries (as produced by ActionRegistry.get_action_log) for history reconstruction.
        Optionally provide a registry (defaults to global registry) to dispatch actions.
        """
        if registry is None:
            from api.actions import registry as global_registry
            registry = global_registry
        for entry in action_log:
            action_id = entry['action_id']
            context = entry['context']
            registry.execute(action_id, context)
    BACKUP_DIRNAME = "backups"
    BACKUP_LIMIT = 10  # Max number of backups to keep

    def backup_project(self, directory=None):
        """Create a timestamped backup of the current harness."""
        import os, datetime, shutil
        dirpath = directory or (os.path.dirname(self.current_file) if self.current_file else os.getcwd())
        backup_dir = Path(dirpath) / self.BACKUP_DIRNAME
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.yaml"
        data = self.harness.to_dict()
        with open(backup_file, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        # Rotate old backups
        backups = sorted(backup_dir.glob("backup_*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[self.BACKUP_LIMIT:]:
            old.unlink()
        return backup_file

    def list_backups(self, directory=None):
        """List available backup files, newest first."""
        import os
        dirpath = directory or (os.path.dirname(self.current_file) if self.current_file else os.getcwd())
        backup_dir = Path(dirpath) / self.BACKUP_DIRNAME
        if not backup_dir.exists():
            return []
        return sorted(backup_dir.glob("backup_*.yaml"), key=lambda p: p.stat().st_mtime, reverse=True)

    def restore_backup(self, backup_path):
        """Restore harness from a backup file."""
        with open(backup_path, 'r') as f:
            data = yaml.safe_load(f)
        self.harness = Harness.from_dict(data)
        self.dirty = True
        self.observer.dispatch("model_changed", {"action": "restore_backup"})
        return self.harness
    AUTOSAVE_FILENAME = ".autosave.yaml"

    def autosave(self, directory=None):
        """Write a snapshot of the current harness to an autosave file."""
        import os
        dirpath = directory or (os.path.dirname(self.current_file) if self.current_file else os.getcwd())
        path = Path(dirpath) / self.AUTOSAVE_FILENAME
        data = self.harness.to_dict()
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        return path

    def clear_autosave(self, directory=None):
        """Remove the autosave file if it exists."""
        import os
        dirpath = directory or (os.path.dirname(self.current_file) if self.current_file else os.getcwd())
        path = Path(dirpath) / self.AUTOSAVE_FILENAME
        if path.exists():
            path.unlink()

    def restore_autosave(self, directory=None):
        """Restore harness from the autosave file if it exists."""
        import os
        dirpath = directory or (os.path.dirname(self.current_file) if self.current_file else os.getcwd())
        path = Path(dirpath) / self.AUTOSAVE_FILENAME
        if not path.exists():
            raise FileNotFoundError(f"No autosave file found at {path}")
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        self.harness = Harness.from_dict(data)
        self.dirty = True
        self.observer.dispatch("model_changed", {"action": "restore_autosave"})
        return self.harness
    """
    Application context for managing the harness, file state, observer, and undo stack.
    Provides project-level operations and state tracking.
    """
    def __init__(self, harness: Harness = None):
        """
        Initialize the Context with a harness, observer, and undo stack.
        Args:
            harness (Harness, optional): The harness to use. Defaults to a new Harness.
        """
        self.harness = harness or Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False
        # Event Bus
        self.observer = Observer()
        # Undo Stack (single implementation)
        self.undo_stack = UndoStack()

    def mark_clean(self):
        """Mark the context as clean (not dirty)."""
        self.dirty = False

    @property
    def is_dirty(self):
        """Return whether the context is dirty (has unsaved changes)."""
        return self.dirty

    @is_dirty.setter
    def is_dirty(self, value):
        """Set the dirty state of the context."""
        self.dirty = value

    def new_project(self):
        """Reset the context to a new project with a fresh harness."""
        self.harness = Harness(meta={"name": "New Harness", "trunk_length_mm": 1000})
        self.current_file = None
        self.dirty = False

    def mark_dirty(self):
        """Mark the context as dirty and clear undo stack, dispatching a model_changed event."""
        self.dirty = True
        self.undo_stack.clear()
        self.observer.dispatch("model_changed", {"action": "new_project"})

    def load(self, path: Path):
        """Load a harness from the given file path."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Harness file not found: {path}")

        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        # Coerce devices to DeviceList if needed
        if data and 'devices' in data:
            from core.harness import DeviceList
            from core.device import Device
            if not isinstance(data['devices'], DeviceList):
                devices = []
                for d in data['devices']:
                    if isinstance(d, dict):
                        devices.append(Device(**d))
                    else:
                        devices.append(d)
                data['devices'] = DeviceList(devices)
            self.harness = Harness.from_dict(data)
        self.current_file = path
        self.dirty = False
        self.observer.dispatch("model_changed", {"action": "load"})

    def save_as(self, path: Path):
        """
        Save the current harness to a new file path.
        Args:
            path (Path): The file path to save the harness to.
        """
        path = Path(path)
        self.harness.increment_revision()
        data = self.harness.to_dict()
        
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
            
        self.current_file = path
        self.dirty = False

# Backward compatibility for legacy imports
ProjectContext = Context

# Global singleton context for API and UI access
global_context = Context()