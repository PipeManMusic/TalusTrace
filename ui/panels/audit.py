from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from api.manager import APIManager

class AuditPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.list = QListWidget()
        self.layout.addWidget(self.list)

    def add_violation(self, violation):
        """Adds a violation to the list (used by Controller)."""
        text = f"{violation.get('type', 'Error')}: {violation.get('message', '')}"
        item = QListWidgetItem(text)
        item.setData(100, violation) # Store user role data
        self.list.addItem(item)

    def on_zoom_clicked(self, violation):
        """
        Handles the user clicking 'Zoom' on a specific violation.
        1. Selects the offending item.
        2. Dispatches a zoom request.
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