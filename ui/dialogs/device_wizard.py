from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class DeviceWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device Wizard")
        layout = QVBoxLayout(self)

        self.name_label = QLabel("Device Name:")
        layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        self.accept_button = QPushButton("Create")
        self.accept_button.setEnabled(False)
        layout.addWidget(self.accept_button)

        self.name_input.textChanged.connect(self._on_name_changed)
        self.accept_button.clicked.connect(self.accept)

    def _on_name_changed(self, text):
        self.accept_button.setEnabled(self.validate())

    def validate(self):
        return bool(self.name_input.text().strip())

    def accept(self):
        from api.manager import APIManager
        from core.device import Device
        name = self.name_input.text().strip()
        if name:
            api = APIManager.get_instance()
            new_device = Device(label=name)
            api.context.harness.devices.append(new_device)
        super().accept()
