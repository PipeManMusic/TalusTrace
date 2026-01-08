import yaml
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction
from api.actions import registry

class LayoutManager:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def create_toolbar(self, parent=None):
        toolbar_cfg = self.config.get('toolbar', {})
        toolbar = QToolBar(parent)
        if not toolbar_cfg.get('visible', True):
            toolbar.hide()
        for item in toolbar_cfg.get('items', []):
            if item.get('separator'):
                toolbar.addSeparator()
            elif 'command' in item:
                cmd = item['command']
                action = QAction(cmd, toolbar)
                action.setData(cmd)
                # Optionally set icon, tooltip, etc. from registry
                toolbar.addAction(action)
        return toolbar
