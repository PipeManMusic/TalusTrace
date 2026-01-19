import yaml
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QAction
from api.actions import registry

class ContextMenuManager:
    def __init__(self, layout_cfg, actions_map):
        self.context_menu_cfg = layout_cfg.get('context_menu', {})
        self.actions_map = actions_map

    def build_menu(self, item_type, parent=None):
        menu_cfg = self.context_menu_cfg.get(item_type, [])
        if not menu_cfg:
            return None
        menu = QMenu(parent)
        for entry in menu_cfg:
            if entry.get('separator'):
                menu.addSeparator()
            elif 'command' in entry:
                cmd_id = entry['command']
                meta = self.actions_map.get(cmd_id, {})
                from ui.i18n import I18N
                label = I18N.get(cmd_id, meta.get('label', cmd_id.split('.')[-1].replace('_', ' ').title()))
                action = QAction(label, menu)
                action.setData(cmd_id)
                if 'tooltip' in meta:
                    action.setToolTip(meta['tooltip'])
                if entry.get('style') == 'danger':
                    action.setProperty('style', 'danger')
                action.triggered.connect(lambda checked=False, cid=cmd_id: registry.execute(cid))
                menu.addAction(action)
        return menu
