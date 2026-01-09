from unittest.mock import patch, MagicMock
from api.actions import registry

def test_wizard_action_launches_dialog():
    """PH6-UI.5: The device creation action must open the Wizard dialog."""
    # Patch DeviceWizard before importing api.commands
    with patch('ui.dialogs.device_wizard.DeviceWizard') as MockWizard:
        import api.commands  # Ensure device.create_wizard is registered after patch
        # Configure the mock instance to handle the .exec() call
        mock_instance = MockWizard.return_value
        mock_instance.exec = MagicMock(return_value=1)
        # Execute the action registered in the api.actions registry
        registry.execute("device.create_wizard")
        # Verify the Wizard was instantiated and exec() was called once
        assert MockWizard.called, "DeviceWizard was not instantiated by the action"
        assert mock_instance.exec.called, "DeviceWizard.exec() was not called"