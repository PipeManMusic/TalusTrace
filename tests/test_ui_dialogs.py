import pytest
from ui.dialogs.device_wizard import DeviceWizard

def test_device_wizard_validation(qtbot):
    """PH5-DEV.1: Wizard should require a Name before accepting."""
    dlg = DeviceWizard()
    qtbot.add_widget(dlg)
    
    # Initial state: Invalid (Name empty)
    assert dlg.validate() is False
    assert dlg.accept_button.isEnabled() is False
    
    # Enter Name
    dlg.name_input.setText("Test Connector")
    assert dlg.validate() is True