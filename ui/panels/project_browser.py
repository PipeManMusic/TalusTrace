from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from api.manager import APIManager

class ProjectBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Harness Components")
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)
        
        # Subscribe to updates
        self.api.subscribe("selection_changed", self.on_selection_changed)
        # In a real app, you'd subscribe to "model_changed" too
        
        self.refresh()

    def refresh(self):
        self.tree.clear()
        harness = self.api.context.harness
        if not harness: return
        
        # Devices Group
        dev_group = QTreeWidgetItem(self.tree, ["Devices"])
        dev_group.setExpanded(True)
        for dev in harness.devices:
            item = QTreeWidgetItem(dev_group, [dev.id])
            item.setData(0, 100, dev.id) # Store ID
            
        # Wires Group
        wire_group = QTreeWidgetItem(self.tree, ["Wires"])
        wire_group.setExpanded(True)
        for wire in harness.wires:
            lbl = f"{wire.from_conn} -> {wire.to_conn}"
            item = QTreeWidgetItem(wire_group, [lbl])
            item.setData(0, 100, getattr(wire, 'id', ''))

    def on_selection_changed(self, data):
        # Simple refresh for now to reflect changes
        # A robust implementation would just highlight the row
        self.refresh()
