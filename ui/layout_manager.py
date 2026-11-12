
"""Layout manager for Talus Trace UI, handling dock widgets and layout persistence."""

import yaml
import os
from PySide6.QtWidgets import QMenuBar, QMenu, QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

class LayoutManager:
    """Creates and manages UI layout elements (menubar, toolbar) from config."""
    def __init__(self, config_path=None):
        """Initialize LayoutManager with optional config path."""
        # Use standard config file - edits to source config are reflected at runtime
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
        """Create a QMenuBar for the given window using the loaded config (UUID-driven)."""
        from ui.i18n import I18N
        from PySide6.QtGui import QKeySequence
        menubar = QMenuBar(window)
        menu_configs = self.config.get('menubar', [])
        # Build reverse map: action_id -> shortcut string from keymap
        shortcut_map = self._load_shortcut_map()
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
                    if item_conf.get('type') == 'recent_files':
                        submenu = QMenu(item_conf.get('label', 'Open Recent'), window)
                        self._populate_recent_menu(submenu, window)
                        submenu.aboutToShow.connect(
                            lambda m=submenu, w=window: self._populate_recent_menu(m, w))
                        menu.addMenu(submenu)
                        continue
                    uuid = item_conf.get('uuid')
                    if uuid:
                        label = I18N.get(uuid, uuid)
                        action = QAction(label, window)
                        action.setData(uuid)
                        if uuid in shortcut_map:
                            action.setShortcut(QKeySequence(shortcut_map[uuid]))
                        def handler(checked=False, *args, uuid=uuid, **kwargs):
                            """Execute an action when triggered from the menu."""
                            from api.actions import registry
                            context = getattr(window, 'api', None)
                            registry.execute(uuid, window)
                        action.triggered.connect(handler)
                        menu.addAction(action)
                    elif 'command' in item_conf:
                        # fallback for legacy
                        cmd_id = item_conf.get('command')
                        label = item_conf.get('label', cmd_id)
                        action = QAction(I18N.get(cmd_id, label), window)
                        action.setData(cmd_id)
                        if cmd_id in shortcut_map:
                            action.setShortcut(QKeySequence(shortcut_map[cmd_id]))
                        def handler(checked=False, *args, cmd_id=cmd_id, **kwargs):
                            """Execute a legacy command action when triggered from the menu."""
                            from api.actions import registry
                            context = getattr(window, 'api', None)
                            registry.execute(cmd_id, window)
                        action.triggered.connect(handler)
                        menu.addAction(action)
        # Add shortcuts that aren't in any menu as application-wide QActions
        menu_uuids = set()
        for menu_conf in menu_configs:
            for item_conf in menu_conf.get('items', []):
                if isinstance(item_conf, dict):
                    uid = item_conf.get('uuid') or item_conf.get('command')
                    if uid:
                        menu_uuids.add(uid)
        for action_id, shortcut_str in shortcut_map.items():
            if action_id not in menu_uuids:
                action = QAction(action_id, window)
                action.setShortcut(QKeySequence(shortcut_str))
                action.setShortcutContext(Qt.ApplicationShortcut)
                def handler(checked=False, *args, aid=action_id, **kwargs):
                    """Execute an application-wide shortcut action."""
                    from api.actions import registry
                    registry.execute(aid, window)
                action.triggered.connect(handler)
                window.addAction(action)
        return menubar

    def _load_shortcut_map(self):
        """Load keymap.yaml and return a dict mapping action_id -> shortcut string."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        keymap_path = os.path.join(base_dir, "resources", "config", "keymap.yaml")
        try:
            with open(keymap_path, 'r') as f:
                keymap = yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        # Build reverse map: action_id -> first shortcut string
        result = {}
        for shortcut_str, action_id in (keymap.get('global') or {}).items():
            if action_id not in result:
                result[action_id] = shortcut_str
        return result

    def _populate_recent_menu(self, menu, window):
        """Populate a QMenu with recent file entries."""
        from api.commands.file import get_recent_files, open_recent_file
        menu.clear()
        recent = get_recent_files()
        if not recent:
            action = menu.addAction("(No recent files)")
            action.setEnabled(False)
            return
        for filepath in recent:
            action = menu.addAction(os.path.basename(filepath))
            action.setToolTip(filepath)
            action.triggered.connect(
                lambda checked=False, p=filepath: open_recent_file(p))

    def create_toolbar(self, window):
        """Create a QToolBar for the given window using the loaded config (UUID-driven)."""
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
                uuid = item_conf
                label = uuid
            elif isinstance(item_conf, dict):
                if item_conf.get('type') == 'separator':
                    toolbar.addSeparator()
                    continue
                uuid = item_conf.get('uuid')
                if uuid:
                    label = I18N.get(uuid, uuid)
                else:
                    uuid = item_conf.get('command')
                    label = item_conf.get('label', uuid)
            else:
                continue
            action = QAction(I18N.get(uuid, label), window)
            action.setData(uuid)
            def handler(checked=False, *args, uuid=uuid, **kwargs):
                """Execute an action and emit signal when triggered."""
                from api.actions import dispatch_action, registry
                dispatch_action(uuid)
                registry.action_triggered.emit(uuid, None)
            action.triggered.connect(handler)
            toolbar.addAction(action)
        return toolbar