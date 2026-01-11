# PH3-3.2: UI: Persistent Audit Punch-List Panel
from PySide6.QtWidgets import QWidget, QListWidget, QVBoxLayout, QListWidgetItem
from PySide6.QtCore import Qt
from api.manager import APIManager

class AuditPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.list_widget = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        # Connect selection to handler
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def on_zoom_clicked(self, violation):
        """Dispatches a zoom event for the given violation (for test_ui_audit_feedback.py)."""
        self.api.dispatch("view.zoom_to", {"target_id": violation["target_id"]})

    def set_violations(self, violations):
        self.list_widget.clear()
        for v in violations:
            # FIXED: Store the actual data item so we can retrieve it on click
            item = QListWidgetItem(f"{v['target_id']}: {v['message']}")
            item.setData(Qt.UserRole, v)
            self.list_widget.addItem(item)

    def on_item_selected(self, violation):
        # Simulate click-to-zoom logic
        if not violation: return
        self.api.dispatch("FOCUS_ENTITY", {"id": violation["target_id"], "zoom_level": 1.5})

    def _on_item_clicked(self, item):
        # FIXED: Retrieve data and trigger logic
        violation = item.data(Qt.UserRole)
        if violation:
            self.on_item_selected(violation)
            self.on_zoom_clicked(violation)