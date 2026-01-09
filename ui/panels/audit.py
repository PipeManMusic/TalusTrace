# PH3-3.2: UI: Persistent Audit Punch-List Panel
from PySide6.QtWidgets import QWidget, QListWidget, QVBoxLayout
from api.manager import APIManager


class AuditPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.list_widget = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        # For demo, connect selection to handler
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def on_zoom_clicked(self, violation):
        """Dispatches a zoom event for the given violation (for test_ui_audit_feedback.py)."""
        self.api.dispatch("view.zoom_to", {"target_id": violation["id"]})

    def set_violations(self, violations):
        self.list_widget.clear()
        for v in violations:
            self.list_widget.addItem(f"{v['target_id']}: {v['message']}")

    def on_item_selected(self, violation):
        # Simulate click-to-zoom logic
        self.api.dispatch("FOCUS_ENTITY", {"id": violation["target_id"], "zoom_level": 1.5})

    def _on_item_clicked(self, item):
        # In a real app, map item back to violation data
        # Here, just a stub for UI wiring
        pass
