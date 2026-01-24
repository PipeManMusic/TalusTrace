"""
Context menu manager for Talus Trace UI.

Manages context menu creation and execution based on selection state and config.
"""

from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction, QCursor
from api.manager import APIManager
from api.actions import registry

class ContextMenuManager:
    """Manages context menu creation and execution based on selection state and config."""
    def __init__(self, config=None, actions_map=None):
        """Initialize ContextMenuManager with optional config and actions map."""
        self.config = config or {}
        # Map of "action_id" -> {"label": "Display Name", "action": "command.id"}
        self.actions_map = actions_map or {}

    def build_menu(self, menu_type=None, parent=None):
        """
        Build and return a QMenu for the given menu_type using config or actions_map.
        If menu_type is None, falls back to actions_map for generic menu.
        """
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction
        menu = QMenu(parent)
        # Use YAML config for context menus if available
        context_menus = self.config.get('context_menu', {}) if self.config else {}
        if menu_type and menu_type in context_menus:
            for entry in context_menus[menu_type]:
                if entry.get('separator', False):
                    menu.addSeparator()
                elif 'command' in entry:
                    cmd_id = entry['command']
                    details = self.actions_map.get(cmd_id, {})
                    label = details.get('label', cmd_id)
                    action = QAction(label, menu)
                    action.setData(cmd_id)
                    action.triggered.connect(lambda checked=False, cid=cmd_id: self._execute(cid))
                    menu.addAction(action)
        elif self.actions_map:
            for key, details in self.actions_map.items():
                label = details.get("label", key)
                cmd_id = details.get("action", key)
                action = QAction(label, menu)
                action.setData(cmd_id)
                action.triggered.connect(lambda checked=False, cid=cmd_id: self._execute(cid))
                menu.addAction(action)
        else:
            action = QAction("No Actions Configured", menu)
            action.setEnabled(False)
            menu.addAction(action)
        return menu

    def show_context_menu(self, event):
        """Build and display the context menu at the mouse position."""
        menu = self.build_menu()
        if hasattr(event, 'globalPos'):
            menu.exec(event.globalPos())
        elif hasattr(event, 'screenPos'):
            menu.exec(event.screenPos())
        else:
            menu.exec(QCursor.pos())

    def _execute(self, command_id):
        """Helper to run the command via the API registry."""
        # Debug output removed
        
        try:
            # Check if command exists in the global registry
            if command_id in registry:
                api = APIManager.get_instance()
                # Execute command, passing the context
                registry.execute(command_id, api.context)
            else:
                pass
        except Exception as e:
            pass