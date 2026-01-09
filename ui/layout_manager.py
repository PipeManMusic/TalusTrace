import yaml
from pathlib import Path
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from api.actions import registry

class LayoutManager:
    def __init__(self, layout_path="resources/config/ui_layout.yaml", actions_path="resources/config/actions.yaml", config_path=None):
        # Allow test to override using config_path kwarg
        final_layout_path = config_path or layout_path
        
        self.layout_cfg = self._load_yaml(final_layout_path)
        self.actions_map = self._load_actions_map(actions_path)

    def _load_yaml(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            return {}

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