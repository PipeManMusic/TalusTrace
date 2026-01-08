import yaml
from pathlib import Path
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from api.actions import registry

class LayoutManager:
    def __init__(self, layout_path="resources/config/ui_layout.yaml", actions_path="resources/config/actions.yaml"):
        self.layout_cfg = self._load_yaml(layout_path)
        self.actions_map = self._load_actions_map(actions_path)

    def _load_yaml(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Config Load Error ({path}): {e}")
            return {}

    def _load_actions_map(self, path):
        """
        Creates a lookup dictionary: {'file.save': {'label': 'Save', 'icon': 'save.svg'}}
        """
        data = self._load_yaml(path)
        return {cmd['id']: cmd for cmd in data.get('commands', [])}

    def create_toolbar(self, parent=None):
        toolbar_cfg = self.layout_cfg.get('toolbar', {})
        if not toolbar_cfg:
            return None

        toolbar = QToolBar(parent)
        toolbar.setWindowTitle("Main Toolbar")
        
        # VISIBILITY FIX: Force text to show alongside icons
        # This ensures buttons are visible even if icons are missing
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        if not toolbar_cfg.get('visible', True):
            toolbar.hide()
            
        for item in toolbar_cfg.get('items', []):
            if item.get('separator'):
                toolbar.addSeparator()
            elif 'command' in item:
                cmd_id = item['command']
                self._add_action(toolbar, cmd_id)
                
        return toolbar

    def _add_action(self, toolbar, cmd_id):
        # 1. Get Metadata (Label, Icon, Tooltip)
        meta = self.actions_map.get(cmd_id, {})
        
        # Fallback Label if missing in YAML
        label = meta.get('label', cmd_id.split('.')[-1].replace('_', ' ').title())
        
        action = QAction(label, toolbar)
        action.setData(cmd_id)
        
        # 2. Set Icon (if exists)
        icon_name = meta.get('icon')
        if icon_name:
            # Assumes icons are in resources/icons/
            icon_path = Path("resources/icons") / icon_name
            if icon_path.exists():
                action.setIcon(QIcon(str(icon_path)))
        
        # 3. Set Tooltip
        if 'tooltip' in meta:
            action.setToolTip(meta['tooltip'])
            
        # 4. Connect Logic
        # We use a default arg (cid=cmd_id) to capture the variable closure correctly
        action.triggered.connect(lambda checked=False, cid=cmd_id: registry.execute(cid))
        
        toolbar.addAction(action)