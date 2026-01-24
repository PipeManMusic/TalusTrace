"""
Device wizard dialog for Talus Trace UI.

Allows users to create a new device by entering ID and name.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class DeviceWizard(QDialog):
    """Dialog for creating a new device with ID and name."""
    def __init__(self, parent=None):
        """Initialize the device wizard dialog and build the UI."""
        super().__init__(parent)
        from ui.i18n import I18N
        self.setWindowTitle(I18N.get('device_wizard_title'))
        layout = QVBoxLayout(self)


        self.id_label = QLabel(I18N.get('device_id_label', 'Device ID'))
        layout.addWidget(self.id_label)
        self.id_input = QLineEdit()
        layout.addWidget(self.id_input)

        self.name_label = QLabel(I18N.get('device_name_label'))
        layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        self.accept_button = QPushButton(I18N.get('create_button'))
        self.accept_button.setEnabled(False)
        layout.addWidget(self.accept_button)

        self.id_input.textChanged.connect(self._on_name_changed)
        self.name_input.textChanged.connect(self._on_name_changed)
        self.accept_button.clicked.connect(self.accept)

    def _on_name_changed(self, text):
        """Enable the accept button if both fields are valid."""
        self.accept_button.setEnabled(self.validate())

    def validate(self):
        """Return True if both ID and name fields are non-empty."""
        return bool(self.id_input.text().strip()) and bool(self.name_input.text().strip())

    def accept(self):
        """Create the device, add it to the context, and refresh the canvas."""
        from api.manager import APIManager
        from core.device import Device
        from api.commands.device import AddDeviceCommand
        id_val = self.id_input.text().strip()
        name = self.name_input.text().strip()
        if id_val and name:
            api = APIManager.get_instance()
            new_device = Device(id=id_val, label=name)
            # Use Command Pattern for undo/redo compliance
            if hasattr(api.context, 'undo_stack'):
                api.context.undo_stack.push(AddDeviceCommand(new_device))
            else:
                AddDeviceCommand(new_device).execute()
            # PH6-FIX.5: Trigger canvas refresh
            from PySide6.QtWidgets import QApplication
            window = QApplication.activeWindow()
            if window and hasattr(window, 'canvas'):
                window.canvas.load_harness(api.context.harness)
        super().accept()
