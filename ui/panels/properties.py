from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt
from api.manager import APIManager

class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        
        # Header
        self.header = QLabel("Properties")
        self.header.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        self.layout.addWidget(self.header)
        
        # Form Container
        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.layout.addWidget(self.form_widget)
        
        # State
        self.current_item = None
        
        # Subscribe to Selection Changes
        # (We use the APIManager observer pattern we verified earlier)
        APIManager.get_instance().subscribe(self._on_app_event)

    def _on_app_event(self, event):
        """
        Listens for 'selection_changed' events from the Core.
        """
        if event.get("event_type") == "selection_changed":
            selection = event.get("selection", [])
            if selection:
                # Edit the first selected item
                self.load_item(selection[0])
            else:
                self.clear_panel()

    def load_item(self, device_model):
        """
        Populates the form with Device data.
        """
        self.current_item = device_model
        self._clear_layout()
        
        # ID Field
        self.id_edit = QLineEdit(device_model.id)
        self.id_edit.editingFinished.connect(self._apply_id_change)
        self.form_layout.addRow("ID:", self.id_edit)
        
        # Label Field
        label_val = device_model.meta.get("label", "")
        self.label_edit = QLineEdit(label_val)
        self.label_edit.editingFinished.connect(self._apply_label_change)
        self.form_layout.addRow("Label:", self.label_edit)
        
        # X/Y Readouts (Read Only for now)
        self.form_layout.addRow("X:", QLabel(f"{device_model.x:.2f}"))
        self.form_layout.addRow("Y:", QLabel(f"{device_model.y:.2f}"))

    def _apply_id_change(self):
        if self.current_item:
            new_val = self.id_edit.text()
            print(f">> Property Change: ID {self.current_item.id} -> {new_val}")
            self.current_item.id = new_val
            # TODO: Phase 5 - Trigger Scene Redraw via Signal

    def _apply_label_change(self):
        if self.current_item:
            new_val = self.label_edit.text()
            print(f">> Property Change: Label -> {new_val}")
            self.current_item.meta["label"] = new_val

    def clear_panel(self):
        self.current_item = None
        self._clear_layout()
        self.form_layout.addRow(QLabel("No Selection"))

    def _clear_layout(self):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()