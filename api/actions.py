def dispatch_action(action_id, context=None):
    """
    Dispatches an action by ID using the global registry.
    """
    print(f"dispatch_action called for: {action_id}")
    registry.execute(action_id, context)
import logging
from typing import Callable, Dict, Optional, List
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QObject, Signal


class ActionRegistry(QObject):
    """
    Central command bus. Maps abstract Action IDs (e.g., "edit.move") 
    to concrete Python Callables.
    """
    # Signal: Action ID, Context Data (Optional)
    action_triggered = Signal(str, object)

    def __contains__(self, action_id: str) -> bool:
        """Allow 'if action_id in registry:' check."""
        return action_id in self._actions

    def keys(self):
        """Return list of registered action IDs."""
        return self._actions.keys()

    def __init__(self):
        super().__init__()
        self._actions: Dict[str, Callable] = {}
        self._ui_actions: Dict[str, QAction] = {} # Qt Actions for Menus/Toolbars
        # ...removed logger setup...

    def register(self, action_id: str, func: Callable):
        """
        Decorator or direct call to bind code to an ID.
        """
        self._actions[action_id] = func
        # ...removed debug log...

    def execute(self, action_id: str, context: Optional[object] = None):
        """
        Trigger the logic associated with an ID.
        """
        if action_id in self._actions:
            # ...removed info log...
            try:
                self._actions[action_id](context)
                self.action_triggered.emit(action_id, context)
            except Exception as e:
                # ...removed error log...
                pass
        else:
            # ...removed warning log...
            pass

    def get_qt_action(self, action_id: str) -> Optional[QAction]:
        return self._ui_actions.get(action_id)

# Global Singleton
registry = ActionRegistry()

def register_action(action_id: str):
    """Decorator for easy registration."""
    def decorator(func):
        registry.register(action_id, func)
        return func
    return decorator