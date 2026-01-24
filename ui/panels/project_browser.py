
"""
Project Browser panel for Talus Trace UI.
Displays devices and wires in a tree structure and synchronizes with selection/model changes.
"""
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from api.manager import APIManager
from PySide6.QtCore import Qt # Import needed for item roles if used later

class ProjectBrowser(QWidget):
    """
    ProjectBrowser panel widget for displaying devices and wires in a tree structure.
    Synchronizes with selection and model changes from the APIManager.
    """
    def list_devices(self):
        """
        Return a list of device IDs currently shown in the Devices group.
        Returns:
            list: List of device IDs.
        """
        ids = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group = root.child(i)
            if group.text(0) == "Devices":
                for j in range(group.childCount()):
                    item = group.child(j)
                    dev_id = item.data(0, 100)
                    if dev_id:
                        ids.append(dev_id)
        return ids
    def __init__(self, parent=None):
        """
        Initialize the ProjectBrowser panel and set up the device/wire tree.
        Subscribes to selection and model changes from the APIManager.
        """
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
        if hasattr(self.api, 'subscribe'):
            self.api.subscribe("selection_changed", self.on_selection_changed)
            self.api.subscribe("model_changed", self.refresh)
        self.refresh()

    def refresh(self, data=None):
        """
        Refresh the tree to display the current devices and wires from the API context.
        Args:
            data (optional): Data passed from the model_changed event.
        """
        self.tree.clear()
        if not hasattr(self.api, 'context') or not self.api.context:
            return
        harness = self.api.context.harness
        if not harness:
            return
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
        for wire in getattr(harness, 'wires', []):
            f_conn = getattr(wire, 'from_conn', '?')
            t_conn = getattr(wire, 'to_conn', '?')
            lbl = f"{f_conn} -> {t_conn}"
            item = QTreeWidgetItem(wire_group, [lbl])
            item.setData(0, 100, getattr(wire, 'id', ''))

    def on_selection_changed(self, data):
        """
        Handle selection change events from the APIManager.
        Args:
            data: Event data (not used).
        """
        # Placeholder for selection sync logic
        pass