from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from api.manager import APIManager

# FIXED: Renamed to match other panels
class ProjectBrowserPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Harness Components")
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)
        
        # Subscriptions
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
            display_text = f"{dev.id} ({dev.label})" if dev.label else dev.id
            item = QTreeWidgetItem(dev_group, [display_text])
            item.setData(0, 100, dev.id) 
            
        # Wires
        wire_group = QTreeWidgetItem(self.tree, ["Wires"])
        wire_group.setExpanded(True)
        for wire in harness.wires:
            lbl = f"{wire.from_conn} -> {wire.to_conn}"
            item = QTreeWidgetItem(wire_group, [lbl])
            item.setData(0, 100, getattr(wire, 'id', ''))

    def on_selection_changed(self, data):
        self.refresh()