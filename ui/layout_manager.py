import yaml
from pathlib import Path
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from api.actions import registry

class LayoutManager:
    def get_context_menu_manager(self):
        from ui.context_menu_manager import ContextMenuManager
        return ContextMenuManager(self.layout_cfg, self.actions_map)

    def create_menubar(self, parent=None):
        from PySide6.QtWidgets import QMenuBar, QMenu
        menubar_cfg = self.layout_cfg.get('menubar', [])
        menubar = QMenuBar(parent)
        for menu_def in menubar_cfg:
            menu = QMenu(menu_def.get('label', 'Menu'), menubar)
            for item in menu_def.get('items', []):
                if 'command' in item:
                    cmd_id = item['command']
                    meta = self.actions_map.get(cmd_id, {})
                    label = meta.get('label', cmd_id.split('.')[-1].replace('_', ' ').title())
                    action = QAction(label, menu)
                    action.setData(cmd_id)
                    if 'tooltip' in meta:
                        action.setToolTip(meta['tooltip'])
                    action.triggered.connect(lambda checked=False, cid=cmd_id: registry.execute(cid))
                    menu.addAction(action)
                elif item.get('separator'):
                    menu.addSeparator()
            menubar.addMenu(menu)
        return menubar

    def __init__(self, layout_path="resources/config/ui_layout.yaml", actions_path="resources/config/actions.yaml", config_path=None):
        # Allow test to override using config_path kwarg
        final_layout_path = config_path or layout_path
        self.layout_cfg = self._load_yaml(final_layout_path)
        self.actions_map = self._load_actions_map(actions_path)

    def _load_yaml(self, path):
        from resources.defaults import DEFAULT_LAYOUT
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                if not data or not isinstance(data, dict):
                    return DEFAULT_LAYOUT.copy()
                return data
        except Exception:
            return DEFAULT_LAYOUT.copy()

    def _load_actions_map(self, path):
        data = self._load_yaml(path)
        commands = data.get('commands', [])
        return {cmd['id']: cmd for cmd in commands}

    def create_toolbar(self, parent=None):
        toolbar_cfg = self.layout_cfg.get('toolbar', {})
        if not toolbar_cfg:
            return None

        toolbar = QToolBar(parent)
        toolbar.setWindowTitle("Main Toolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        if not toolbar_cfg.get('visible', True):
            toolbar.hide()

        items = toolbar_cfg.get('items', [])
        for item in items:
            if item.get('separator'):
                toolbar.addSeparator()
            elif 'command' in item:
                cmd_id = item['command']
                self._add_action(toolbar, cmd_id)

        return toolbar

    def _add_action(self, toolbar, cmd_id):
        meta = self.actions_map.get(cmd_id, {})
        label = meta.get('label', cmd_id.split('.')[-1].replace('_', ' ').title())
        action = QAction(label, toolbar)
        action.setData(cmd_id)

        icon_name = meta.get('icon')
        if icon_name:
            icon_path = Path("resources/icons") / icon_name
            if icon_path.exists():
                action.setIcon(QIcon(str(icon_path)))

        if 'tooltip' in meta:
            action.setToolTip(meta['tooltip'])

        action.triggered.connect(lambda checked=False, cid=cmd_id: registry.execute(cid))
        toolbar.addAction(action)