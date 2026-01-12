import yaml
import os
from pathlib import Path
from PySide6.QtWidgets import QToolBar, QMenuBar, QMenu
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from api.actions import registry

class LayoutManager:
    def __init__(self, layout_path="resources/config/ui_layout.yaml", actions_path="resources/config/actions.yaml"):
        self.layout_cfg = self._load_yaml(layout_path)
        self.actions_map = self._load_actions_map(actions_path)

    def _load_yaml(self, path):
        if not os.path.exists(path):
            print(f">> Warning: Config file not found: {path}")
            return {}
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f">> Error loading {path}: {e}")
            return {}

    def _load_actions_map(self, path):
        data = self._load_yaml(path)
        commands = data.get('commands', [])
        # Create a lookup dict: "file.new" -> {label: "New", icon: "new.png", ...}
        if isinstance(commands, list):
            return {cmd['id']: cmd for cmd in commands}
        return {}

    def create_menubar(self, parent=None):
        menubar = QMenuBar(parent)
        menu_defs = self.layout_cfg.get('menubar', [])
        
        for menu_def in menu_defs:
            label = menu_def.get('label', 'Untitled')
            menu = QMenu(label, menubar)
            
            for item in menu_def.get('items', []):
                self._process_item(menu, item)
                
            menubar.addMenu(menu)
        return menubar

    def create_toolbar(self, parent=None):
        toolbar_def = self.layout_cfg.get('toolbar', {})
        if not toolbar_def.get('visible', True):
            return None
            
        toolbar = QToolBar("Main Toolbar", parent)
        toolbar.setObjectName("MainToolbar")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        for item in toolbar_def.get('items', []):
            self._process_item(toolbar, item)
            
        return toolbar

    def _process_item(self, container, item):
        """Helper to create actions from config items."""
        if item.get('separator'):
            container.addSeparator()
            return

        cmd_id = item.get('command')
        if not cmd_id: return

        # 1. Get Metadata (Config > Defaults)
        meta = self.actions_map.get(cmd_id, {})
        label = item.get('label', meta.get('label', cmd_id.split('.')[-1].title()))
        icon_name = item.get('icon', meta.get('icon'))
        tooltip = item.get('tooltip', meta.get('tooltip'))
        shortcut = item.get('shortcut', meta.get('default_key'))

        # 2. Create Action
        action = QAction(label, container)
        action.setData(cmd_id)
        
        if icon_name:
            # Check resource path
            icon_path = Path(f"resources/icons/{icon_name}")
            if icon_path.exists():
                action.setIcon(QIcon(str(icon_path)))
        
        if tooltip: action.setToolTip(tooltip)
        if shortcut: action.setShortcut(shortcut)

        # 3. Connect to Registry
        action.triggered.connect(lambda chk=False, cid=cmd_id: registry.execute(cid))
        container.addAction(action)