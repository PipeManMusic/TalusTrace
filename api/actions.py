"""
Action system and registry for Talus Trace API.
Provides transaction management, action dispatch, registration, and project/session management utilities.
"""
import os, yaml
from pathlib import Path
import logging
from typing import Callable, Dict, Optional, List
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QObject, Signal

# --- ActionRegistry class (full, correct version) ---
class ActionRegistry(QObject):
    """
    Central command bus. Maps abstract Action IDs (e.g., "edit.move") 
    to concrete Python Callables.
    """
    action_triggered = Signal(str, object)
    def __init__(self, log_path=None):
        """Initialize the ActionRegistry with optional logging."""
        super().__init__()
        self._actions: Dict[str, Callable] = {}
        self._ui_actions: Dict[str, QAction] = {}
        self._action_log: List[dict] = []
        self._action_meta: Dict[str, dict] = {}
        if log_path is not None:
            from infra.action_logger import ActionLogger
            self._logger = ActionLogger(Path(log_path))
        else:
            self._logger = None

    def get_action_log(self) -> List[dict]:
        """Return the action log as a list of dicts."""
        return list(self._action_log)

    def clear_action_log(self):
        """Clear the action log."""
        self._action_log.clear()

    def __contains__(self, action_id: str) -> bool:
        """Return True if the action_id is registered."""
        return action_id in self._actions

    def keys(self):
        """Return all registered action IDs."""
        return self._actions.keys()

    def register(self, action_id: str, func: Callable = None, **meta):
        """Register an action handler for the given action_id."""
        def do_register(f):
            """Inner function to perform the actual registration."""
            self._actions[action_id] = f
            if meta:
                self._action_meta[action_id] = meta
            return f
        if func is None:
            return do_register
        else:
            return do_register(func)

    def get_action_metadata(self, action_id: str) -> dict:
        """Return metadata for a registered action."""
        return self._action_meta.get(action_id, {})

    def list_registered_actions(self, with_meta=False):
        """List all registered actions, optionally with metadata."""
        if with_meta:
            return [(aid, self._action_meta.get(aid, {})) for aid in self._actions.keys()]
        return list(self._actions.keys())

    def execute(self, action_id: str, context: Optional[object] = None):
        """Execute the registered action handler for the given action_id."""
        import datetime
        if action_id in self._actions:
            try:
                self._actions[action_id](context)
                self.action_triggered.emit(action_id, context)
                entry = {
                    'action_id': action_id,
                    'context': context,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                self._action_log.append(entry)
                if self._logger:
                    self._logger.log('action', entry)
            except Exception as e:
                raise




registry = ActionRegistry()
def register_ui_action_stubs():
    """Register no-op stubs for all UI actions defined in the YAML config that are not already registered."""
    def _noop(ctx=None):
        """No-op action stub for unimplemented UI actions."""
        pass
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/config/ui_layout.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    action_ids = set()
    # Menubar
    for menu in config.get("menubar", []):
        for item in menu.get("items", []):
            if isinstance(item, dict) and "command" in item:
                action_ids.add(item["command"])
    # Toolbar
    for item in config.get("toolbar", {}).get("items", []):
        if isinstance(item, dict) and "command" in item:
            action_ids.add(item["command"])
    # Context menu
    for section in config.get("context_menu", {}).values():
        for item in section:
            if isinstance(item, dict) and "command" in item:
                action_ids.add(item["command"])
    for _action_id in action_ids:
        if _action_id not in registry._actions:
            registry.register(_action_id, _noop)
register_ui_action_stubs()
"""
Action system and registry for Talus Trace API.
Provides transaction management, action dispatch, registration, and project/session management utilities.
"""
from pathlib import Path

def begin_transaction(description=None):
    """Begin a transaction for grouping undoable actions."""
    """Begin a transaction for grouping undoable actions."""
    ctx = context.global_context
    ctx.undo_stack.begin_transaction(description)

def end_transaction():
    """End the current transaction and push grouped actions as one."""
    """End the current transaction and push grouped actions as one."""
    ctx = context.global_context
    ctx.undo_stack.end_transaction()

def replay_action_log(action_log):
    """Replay a list of action log entries for history reconstruction."""
    """Replay a list of action log entries for history reconstruction."""
    ctx = context.global_context
    return ctx.replay_action_log(action_log)
def dispatch_action(action_id, context=None):
    """Dispatches an action by ID using the global registry."""
    """
    Dispatches an action by ID using the global registry.
    """
    registry.execute(action_id, context)



# --- UI Menu/Toolbar Action Stubs ---
def register_ui_action_stubs():
    """Register no-op stubs for all UI actions defined in the YAML config that are not already registered (duplicate for coverage)."""
    def _noop(ctx=None):
        """No-op action stub for unimplemented UI actions (duplicate for coverage)."""
        pass
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../resources/config/ui_layout.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    action_ids = set()
    # Menubar
    for menu in config.get("menubar", []):
        for item in menu.get("items", []):
            if isinstance(item, dict) and "command" in item:
                action_ids.add(item["command"])
    # Toolbar
    for item in config.get("toolbar", {}).get("items", []):
        if isinstance(item, dict) and "command" in item:
            action_ids.add(item["command"])
    # Context menu
    for section in config.get("context_menu", {}).values():
        for item in section:
            if isinstance(item, dict) and "command" in item:
                action_ids.add(item["command"])
    for _action_id in action_ids:
        if _action_id not in registry._actions:
            registry.register(_action_id, _noop)




    
# Project/session/state management API scaffolding
from infra import context, persistence

def import_project(file_path: str):
    """Import a project from a YAML or JSON file."""
    # Format detection by file extension
    ext = str(file_path).lower().split('.')[-1]
    if ext == 'json':
        return persistence.JSONPersistence.load(file_path)
    return persistence.YAMLPersistence.load(file_path)

def export_project(project, file_path: str):
    """Export the current project to a YAML or JSON file."""
    ext = str(file_path).lower().split('.')[-1]
    if ext == 'json':
        return persistence.JSONPersistence.save(project, file_path)
    return persistence.YAMLPersistence.save(project, file_path)

def autosave_project():
    """Trigger an autosave of the current project/session."""
    # Use the global context; in real app, pass or manage context instance
    ctx = context.Context() if not hasattr(context, 'global_context') else context.global_context
    return ctx.autosave()

def restore_session():
    """Restore the last autosaved session if available."""
    ctx = context.Context() if not hasattr(context, 'global_context') else context.global_context
    return ctx.restore_autosave()

def backup_project():
    """Create a versioned backup of the current project."""
    ctx = context.global_context
    return ctx.backup_project()

def restore_backup(backup_path: str):
    """Restore a project from a backup file."""
    ctx = context.global_context
    return ctx.restore_backup(backup_path)

def atomic_save_project(project, file_path: str):
    """Atomically save the project to disk with validation hooks."""
    # TODO: Add pre/post-save validation hooks
    return persistence.YAMLPersistence.atomic_save(project, file_path)

    def get_qt_action(self, action_id: str) -> Optional[QAction]:
        """
        Get the associated QAction for a registered action ID, if any.
        Args:
            action_id (str): The action ID.
        Returns:
            Optional[QAction]: The QAction instance or None.
        """
        return self._ui_actions.get(action_id)



def register_action(action_id: str):
    """Decorator for easy registration of an action handler with the global registry."""
    """
    Decorator for easy registration of an action handler with the global registry.
    Args:
        action_id (str): The action ID to register.
    Returns:
        Callable: The decorator function.
    """
    def decorator(func):
        """
        Register the decorated function as an action handler for the given action_id.
        Args:
            func (Callable): The function to register.
        Returns:
            Callable: The registered function.
        """
        registry.register(action_id, func)
        return func
    return decorator