from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from api.manager import APIManager
from PySide6.QtCore import Qt # Import needed for item roles if used later

# FIXED: Renamed back to ProjectBrowser to match imports
class ProjectBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        from ui.i18n import I18N
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(I18N.get('project_browser_panel_header'))
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)
        
        # Subscriptions
        # Safety check for methods before subscribing
        if hasattr(self.api, 'subscribe'):
             self.api.subscribe("selection_changed", self.on_selection_changed)
             self.api.subscribe("model_changed", self.refresh)
        
        self.refresh()

    def refresh(self, data=None):
        self.tree.clear()
        
        if not hasattr(self.api, 'context') or not self.api.context: return
        harness = self.api.context.harness
        if not harness: return
        
        # Devices
        dev_group = QTreeWidgetItem(self.tree, ["Devices"])
        dev_group.setExpanded(True)
        for dev in harness.devices:
            display_text = f"{dev.id} ({dev.label})" if hasattr(dev, 'label') and dev.label else dev.id
            item = QTreeWidgetItem(dev_group, [display_text])
            item.setData(0, 100, dev.id) 
            
        # Wires
        wire_group = QTreeWidgetItem(self.tree, ["Wires"])
        wire_group.setExpanded(True)
        # Handle cases where wires might be missing (initial state)
        for wire in getattr(harness, 'wires', []):
            f_conn = getattr(wire, 'from_conn', '?')
            t_conn = getattr(wire, 'to_conn', '?')
            lbl = f"{f_conn} -> {t_conn}"
            item = QTreeWidgetItem(wire_group, [lbl])
            item.setData(0, 100, getattr(wire, 'id', ''))

    def on_selection_changed(self, data):
        # Placeholder for selection sync logic
        pass