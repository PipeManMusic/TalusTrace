import yaml
import os
from PySide6.QtWidgets import QMenuBar, QMenu, QToolBar
from PySide6.QtGui import QAction

class LayoutManager:
    def __init__(self, config_path=None):
        if config_path is None:
             base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
             config_path = os.path.join(base_dir, "resources", "config", "ui_layout.yaml")
             
        self.config_path = config_path
        self.config = {}
        self._load_config()

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.config = {}

    def create_menubar(self, window):
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
                    if cmd_id:
                        action.setData(cmd_id)
                        def handler(checked=False, cmd_id=cmd_id):
                            from api.actions import dispatch_action
                            dispatch_action(cmd_id)
                        action.triggered.connect(handler)
                    menu.addAction(action)
        return menubar

    def create_toolbar(self, window):
        from ui.i18n import I18N
        toolbar = QToolBar(window)
        toolbar.setObjectName("MainToolBar")
        toolbar_section = self.config.get('toolbar', {})
        toolbar_configs = toolbar_section.get('items', [])
        for item_conf in toolbar_configs:
            def connect_handler(action, cmd_id):
                def handler(checked=False):
                    from api.actions import dispatch_action
                    print(f"QAction triggered for: {cmd_id}")
                    dispatch_action(cmd_id)
                action.triggered.connect(handler)

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
            action.setData(cmd_id)
            connect_handler(action, cmd_id)
            toolbar.addAction(action)
        return toolbar