import yaml
from pathlib import Path
from PySide6.QtWidgets import QToolBar, QMenuBar, QMenu
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from api.actions import registry

class LayoutManager:
    def __init__(self, layout_path="resources/config/ui_layout.yaml", actions_path="resources/config/actions.yaml", config_path=None):
        final_layout_path = config_path or layout_path
        self.layout_cfg = self._load_yaml(final_layout_path)
        self.actions_map = self._load_actions_map(actions_path)

    def _load_yaml(self, path):
        # Fallback if file missing
        default = {}
        try:
            if not Path(path).exists(): return default
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else default
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return default

    def _load_actions_map(self, path):
        data = self._load_yaml(path)
        commands = data.get('commands', [])
        return {cmd['id']: cmd for cmd in commands}

    def create_menubar(self, parent=None):
        menubar_cfg = self.layout_cfg.get('menubar', [])
        menubar = QMenuBar(parent)
        for menu_def in menubar_cfg:
            menu = QMenu(menu_def.get('label', 'Menu'), menubar)
            for item in menu_def.get('items', []):
                if 'command' in item:
                    self._add_action_to_container(menu, item['command'], item)
                elif item.get('separator'):
                    menu.addSeparator()
            menubar.addMenu(menu)
        return menubar

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
                self._add_action_to_container(toolbar, item['command'], item)

        return toolbar

    def _add_action_to_container(self, container, cmd_id, override_meta=None):
        """Helper to create QAction and add to Menu or Toolbar."""
        meta = self.actions_map.get(cmd_id, {})
        # Merge overrides (e.g. custom label in layout.yaml)
        if override_meta:
            meta = {**meta, **override_meta}
            
        label = meta.get('label', cmd_id.split('.')[-1].replace('_', ' ').title())
        action = QAction(label, container)
        action.setData(cmd_id)

        # Icon Handling
        icon_name = meta.get('icon')
        if icon_name:
            # Check standard icons first
            from PySide6.QtWidgets import QStyle, QApplication
            if hasattr(QStyle, icon_name):
                action.setIcon(QApplication.style().standardIcon(getattr(QStyle, icon_name)))
            else:
                # Then check file path
                icon_path = Path("resources/icons") / icon_name
                if icon_path.exists():
                    action.setIcon(QIcon(str(icon_path)))

        if 'tooltip' in meta:
            action.setToolTip(meta['tooltip'])
            
        if 'default_key' in meta:
            action.setShortcut(meta['default_key'])

        # BINDING: Connect YAML command ID to API Registry
        action.triggered.connect(lambda checked=False, cid=cmd_id: registry.execute(cid))
        container.addAction(action)
