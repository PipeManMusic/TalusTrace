
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

    @property
    def devices(self):
        """
        Return the list of device models currently in the harness (mirrors what is shown in the browser).
        """
        if hasattr(self.api, 'context') and self.api.context and hasattr(self.api.context, 'harness'):
            return list(getattr(self.api.context.harness, 'devices', []))
        return []
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
            # Subscribe to all *_removed events for live updates
            self.api.subscribe("device_removed", self.refresh)
            self.api.subscribe("wire_removed", self.refresh)
            self.api.subscribe("bundle_removed", self.refresh)
            self.api.subscribe("pin_removed", self.refresh)
        self.refresh()

    def refresh(self, data=None):
        """
        Refresh the tree to display the current devices and wires from the API context.
        Args:
            data (optional): Data passed from the model_changed event.
        """
        from infra.logging import infra_log
        infra_log(f"[ProjectBrowser] refresh called with data={data}", level="debug")
        # If called from a model_changed event, only refresh for device add/remove/delete
        if data and isinstance(data, dict):
            action = data.get('action')
            # Always refresh for device add/remove/delete actions, regardless of item type
            if action in ('remove', 'delete', 'add'):
                pass  # continue to refresh
            else:
                infra_log(f"[ProjectBrowser] refresh: skipping for action={action}", level="debug")
                return
        infra_log(f"[ProjectBrowser] refresh: proceeding to update tree", level="debug")
        self.tree.clear()
        if not hasattr(self.api, 'context') or not self.api.context:
            infra_log(f"[ProjectBrowser] refresh: no api context", level="debug")
            return
        harness = self.api.context.harness
        if not harness:
            infra_log(f"[ProjectBrowser] refresh: no harness", level="debug")
            return
        # Devices
        dev_group = QTreeWidgetItem(self.tree, ["Devices"])
        dev_group.setExpanded(True)
        ids_seen = set()
        for dev in harness.devices:
            infra_log(f"[ProjectBrowser] refresh: device in harness.devices: {getattr(dev, 'id', None)}", level="debug")
            if dev.id in ids_seen:
                import sys
                print(f"[ERROR] Duplicate device ID in project browser: {dev.id}", file=sys.stderr)
                assert False, f"Duplicate device ID in project browser: {dev.id}"
            ids_seen.add(dev.id)
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