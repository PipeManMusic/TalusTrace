from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QLabel
from PySide6.QtCore import Qt

class PinMappingDialog(QDialog):
    DialogCode = QDialog.DialogCode
    def __init__(self, wire_id, connector_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Map Wire {wire_id} to Connector {connector_id}")
        self.selected_pin = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Select pin for wire {wire_id} on connector {connector_id}:"))
        self.pin_selector = QComboBox(self)
        # For demo, populate with mock pins
        self.pin_selector.addItems(["1:A", "1:B", "2:A", "2:B"])
        layout.addWidget(self.pin_selector)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.pin_selector.currentTextChanged.connect(self._on_pin_selected)
        self._on_pin_selected(self.pin_selector.currentText())

    def _on_pin_selected(self, pin):
        self.selected_pin = pin

    def get_selected_pin(self):
        return self.selected_pin
