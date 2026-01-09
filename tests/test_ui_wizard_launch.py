from unittest.mock import patch, MagicMock
from api.actions import registry
from PySide6.QtCore import Qt

def test_wizard_action_launches_dialog(qtbot):
    """PH6-UI.5: The device creation action must open the Wizard dialog and create a device."""
    from ui.dialogs.device_wizard import DeviceWizard
    import api.commands  # Ensure device.create_wizard is registered

    # Patch exec to simulate dialog interaction
    original_exec = DeviceWizard.exec
    def fake_exec(self):
        self.name_input.setText("AutoDevice")
        qtbot.waitUntil(lambda: self.accept_button.isEnabled())
        qtbot.mouseClick(self.accept_button, Qt.LeftButton)
        return 1
    DeviceWizard.exec = fake_exec

    try:
        registry.execute("device.create_wizard")
        # After execution, check that a device was added
        from api.manager import APIManager
        api = APIManager.get_instance()
        assert any(d.label == "AutoDevice" for d in api.context.harness.devices), "Device was not created by wizard."
    finally:
        DeviceWizard.exec = original_exec