
"""
Pin mapping dialog for assigning wires to connector pins in the Talus Trace UI.
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QDialogButtonBox, QLabel
from PySide6.QtCore import Qt

class PinMappingDialog(QDialog):
    """
    Dialog for mapping a wire to a connector pin.
    """
    DialogCode = QDialog.DialogCode
    def __init__(self, wire_id, connector_id, parent=None):
        """
        Initialize the pin mapping dialog for a given wire and connector.
        Args:
            wire_id (str): The ID of the wire to map.
            connector_id (str): The ID of the connector.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        from ui.i18n import I18N
        self.setWindowTitle(I18N.get('pin_mapping_dialog_title', wire_id=wire_id, connector_id=connector_id))
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
        """
        Handle pin selection changes in the combo box.
        Args:
            pin (str): The selected pin.
        """
        self.selected_pin = pin

    def get_selected_pin(self):
        """
        Return the currently selected pin.
        Returns:
            str: The selected pin.
        """
        return self.selected_pin
