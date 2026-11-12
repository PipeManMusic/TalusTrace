
"""
Audit panel for displaying and interacting with audit violations in the Talus Trace UI.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel,
)
from PySide6.QtCore import Qt, QTimer
from api.manager import APIManager

class AuditPanel(QWidget):
    """
    Panel widget for displaying audit violations and providing actions such as zooming to the offending item.
    """
    def __init__(self, parent=None):
        """
        Initialize the AuditPanel and set up the list widget for violations.
        """
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)

        # Header row with title + Run button
        header = QHBoxLayout()
        title = QLabel("Audit")
        title.setStyleSheet("font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        self.run_btn = QPushButton("Run Audit")
        self.run_btn.clicked.connect(self.run_audit)
        header.addWidget(self.run_btn)
        self._layout.addLayout(header)

        self.status_label = QLabel("")
        self._layout.addWidget(self.status_label)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._layout.addWidget(self.list)

        # Debounce timer: coalesce rapid model_changed events into a single
        # audit run and keep the (potentially expensive) audit off the
        # synchronous edit path so a field edit never freezes the UI.
        self._audit_timer = QTimer(self)
        self._audit_timer.setSingleShot(True)
        self._audit_timer.setInterval(150)
        self._audit_timer.timeout.connect(self.run_audit)

        # Subscribe to model changes so we can auto-refresh
        if hasattr(self.api, 'subscribe'):
            self.api.subscribe("model_changed", self._on_model_changed)

        self._violation_count = 0

    def run_audit(self):
        """Run the audit engine against the current harness and display results."""
        from infra.audit import AuditEngine
        self.list.clear()
        harness = getattr(self.api.context, 'harness', None)
        if not harness:
            self.status_label.setText("No harness loaded.")
            self._violation_count = 0
            return

        engine = AuditEngine()  # loads rules from YAML automatically
        violations = engine.run(harness)
        self._violation_count = len(violations)

        if not violations:
            self.status_label.setText("No issues found.")
            return

        self.status_label.setText(f"{len(violations)} issue(s) found.")
        for v in violations:
            self.add_violation(v)

    def add_violation(self, violation):
        """
        Add a violation to the list.
        Args:
            violation: Violation object (Pydantic) or dict.
        """
        if hasattr(violation, 'severity'):
            # Pydantic Violation object
            icon = "⚠" if violation.severity == "WARNING" else "✗" if violation.severity == "ERROR" else "ℹ"
            text = f"{icon} [{violation.severity}] {violation.message}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, {
                'target_id': violation.target_id,
                'severity': violation.severity,
                'message': violation.message,
            })
        else:
            # Legacy dict
            text = f"{violation.get('type', 'Error')}: {violation.get('message', '')}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, violation)
        self.list.addItem(item)

    def _on_item_double_clicked(self, item):
        """Zoom to the offending item on double-click."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.on_zoom_clicked(data)

    def _on_model_changed(self, _data=None):
        """Schedule a debounced audit refresh on model changes.

        Running the audit directly here would execute a full-harness audit on
        the UI thread for every model_changed event (which can fire several
        times per edit), freezing the UI. The single-shot timer collapses
        bursts into one deferred run once edits settle.
        """
        self._audit_timer.start()

    def on_zoom_clicked(self, violation):
        """
        Handle the user clicking 'Zoom' on a specific violation.
        Selects the offending item and dispatches a zoom request.
        Args:
            violation (dict): Violation information containing the target id.
        """
        target_id = violation.get('target_id') or violation.get('id')
        if not target_id:
            return

        api = APIManager.get_instance()

        # 1. Select the item (So the user knows what is being zoomed to)
        api.select([target_id], tool_name="AuditPanel")

        # 2. Trigger Zoom Action (View should listen for this or 'selection_changed')
        api.dispatch("request_zoom_to_selection", {"ids": [target_id]})