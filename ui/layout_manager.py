"""Layout manager for Talus Trace UI, handling dock widgets and layout persistence."""

import yaml
import os
from PySide6.QtWidgets import QMenuBar, QMenu, QToolBar
from PySide6.QtGui import QAction

class LayoutManager:
    """Creates and manages UI layout elements (menubar, toolbar) from config."""
    def __init__(self, config_path=None):
        """Initialize LayoutManager with optional config path."""
        if config_path is None:
             base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
             config_path = os.path.join(base_dir, "resources", "config", "ui_layout.yaml")
             
        self.config_path = config_path
        self.config = {}
        self._load_config()

    def _load_config(self):
        """Load the YAML configuration for UI layout."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.config = {}

    def create_menubar(self, window):
        """Create a QMenuBar for the given window using the loaded config."""
        from ui.i18n import I18N
        menubar = QMenuBar(window)
        menu_configs = self.config.get('menubar', [])
        for menu_conf in menu_configs:
            label = menu_conf.get('label', 'Untitled')
            menu = menubar.addMenu(I18N.get(label, label))
            for item_conf in menu_conf.get('items', []):
                if isinstance(item_conf, str):
                    if item_conf == 'separator':
                        menu.addSeparator()
                    continue
                if isinstance(item_conf, dict):
                    if item_conf.get('type') == 'separator':
                        menu.addSeparator()
                        continue
                    cmd_id = item_conf.get('command')
                    label = item_conf.get('label', cmd_id)
                    action = QAction(I18N.get(cmd_id, label), window)
                    # Always set data for testability
                    action.setData(cmd_id)
                    def handler(checked=False, *args, cmd_id=cmd_id, **kwargs):
                        """Handle layout manager events with provided arguments."""
                        from api.actions import registry
                        context = getattr(window, 'api', None)
                        # For dialog actions, pass the window as context if needed
                        # Always pass the main window as context for all actions
                        registry.execute(cmd_id, window)
                    action.triggered.connect(handler)
                    menu.addAction(action)
        return menubar

    def create_toolbar(self, window):
        """Create a QToolBar for the given window using the loaded config."""
        from ui.i18n import I18N
        toolbar = QToolBar(window)
        toolbar.setObjectName("MainToolBar")
        toolbar_section = self.config.get('toolbar', {})
        toolbar_configs = toolbar_section.get('items', [])
        for item_conf in toolbar_configs:
            if isinstance(item_conf, str):
                if item_conf == 'separator':
                    toolbar.addSeparator()
                    continue
                cmd_id = item_conf
                label = cmd_id
            elif isinstance(item_conf, dict):
                if item_conf.get('type') == 'separator':
                    toolbar.addSeparator()
                    continue
                cmd_id = item_conf.get('command')
                label = item_conf.get('label', cmd_id)
            else:
                continue
            action = QAction(I18N.get(cmd_id, label), window)
            # Always set data for testability
            action.setData(cmd_id)
            def handler(checked=False, *args, cmd_id=cmd_id, **kwargs):
                """Handle toolbar action trigger event and dispatch the command action."""
                from api.actions import dispatch_action, registry
                dispatch_action(cmd_id)
                # Explicitly emit action_triggered for test coverage
                registry.action_triggered.emit(cmd_id, None)
            action.triggered.connect(handler)
            toolbar.addAction(action)
        return toolbar