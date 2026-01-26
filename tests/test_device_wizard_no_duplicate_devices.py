import pytest
from api.manager import APIManager
from ui.dialogs.device_wizard import DeviceWizard
from PySide6.QtCore import Qt

def test_device_wizard_no_duplicate_devices(qtbot):
    """
    Simulate the full UI flow: use DeviceWizard to create a device and ensure only one device is added to the harness.
    Regression test for duplicate device addition in the UI/project browser.
    """
    APIManager.reset()
    api = APIManager.get_instance()
    initial_count = len(api.context.harness.devices)
    wizard = DeviceWizard()
    wizard.name_input.setText("Test Device")
    ok_button = wizard.accept_button
    if ok_button.isEnabled():
        qtbot.mouseClick(ok_button, Qt.LeftButton)
    else:
        wizard.accept()
    # After creation, only one device should be added
    assert len(api.context.harness.devices) == initial_count + 1, (
        f"Expected 1 device added, found {len(api.context.harness.devices) - initial_count}"
    )
    # IDs in harness must be unique
    ids = [dev.id for dev in api.context.harness.devices]
    assert len(ids) == len(set(ids)), "Duplicate device IDs found in harness!"
