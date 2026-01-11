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
        # CRITICAL: Listen for model changes (renaming a label needs to trigger a refresh)
        self.api.subscribe("model_changed", self.refresh)
        
        self.refresh()

    def refresh(self, data=None):
        """Rebuilds the tree view from the Core Model."""
        self.tree.clear()
        harness = self.api.context.harness
        if not harness: return
        
        # Devices Group
        dev_group = QTreeWidgetItem(self.tree, ["Devices"])
        dev_group.setExpanded(True)
        for dev in harness.devices:
            # LOGIC: Show "ID (Label)" if label exists, else "ID"
            display_text = f"{dev.id} ({dev.label})" if dev.label else dev.id
            
            item = QTreeWidgetItem(dev_group, [display_text])
            item.setData(0, 100, dev.id) # Store ID in data column 0, role 100
            
        # Wires Group
        wire_group = QTreeWidgetItem(self.tree, ["Wires"])
        wire_group.setExpanded(True)
        for wire in harness.wires:
            lbl = f"{wire.from_conn} -> {wire.to_conn}"
            item = QTreeWidgetItem(wire_group, [lbl])
            item.setData(0, 100, getattr(wire, 'id', ''))

    def on_selection_changed(self, data):
        # In a full implementation, we would just highlight the row here
        # instead of rebuilding, but rebuilding ensures labels are up to date
        # if the selection change was triggered by a property edit.
        self.refresh()