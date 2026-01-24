
"""
Audit panel for displaying and interacting with audit violations in the Talus Trace UI.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
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
        self.layout = QVBoxLayout(self)
        from ui.i18n import I18N
        self.list = QListWidget()
        self.layout.addWidget(self.list)
        # Optionally set header if needed

    def add_violation(self, violation):
        """
        Add a violation to the list (used by Controller).
        Args:
            violation (dict): Violation information to display.
        """
        text = f"{violation.get('type', 'Error')}: {violation.get('message', '')}"
        item = QListWidgetItem(text)
        item.setData(100, violation) # Store user role data
        self.list.addItem(item)

    def on_zoom_clicked(self, violation):
        """
        Handle the user clicking 'Zoom' on a specific violation.
        Selects the offending item and dispatches a zoom request.
        Args:
            violation (dict): Violation information containing the target id.
        """
        target_id = violation.get('id')
        if not target_id:
            return

        api = APIManager.get_instance()

        # 1. Select the item (So the user knows what is being zoomed to)
        api.select([target_id], tool_name="AuditPanel")

        # 2. Trigger Zoom Action (View should listen for this or 'selection_changed')
        # We dispatch a specific intent so the View knows to focus immediately.
        api.dispatch("request_zoom_to_selection", {"ids": [target_id]})