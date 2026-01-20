import pytest
from ui.dialogs.device_wizard import DeviceWizard

def test_device_wizard_validation(qtbot):
    """PH5-DEV.1: Wizard should require a Name before accepting."""
    import os
    print(f"[DEBUG] DISPLAY={os.environ.get('DISPLAY')}, PYTEST_CURRENT_TEST={os.environ.get('PYTEST_CURRENT_TEST')}")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    dlg = DeviceWizard()
    qtbot.addWidget(dlg)
    # Initial state: Invalid (Name empty)
    assert dlg.validate() is False
    assert dlg.accept_button.isEnabled() is False
    # Enter ID and Name
    dlg.id_input.setText("TEST-001")
    dlg.name_input.setText("Test Connector")
    assert dlg.validate() is True