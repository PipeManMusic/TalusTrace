import pytest
from ui.dialogs.device_wizard import DeviceWizard

def test_device_wizard_validation(qtbot):
    """PH5-DEV.1: Wizard should require a Part ID + Name before accepting.

    Post-refactor the wizard is a QWizard; validation lives on the first
    page via :meth:`QWizardPage.isComplete`.
    """
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    dlg = DeviceWizard()
    qtbot.addWidget(dlg)
    page = dlg.metadata_page
    # Initial state: invalid (both fields empty)
    assert page.isComplete() is False
    # Enter ID and Name
    page.id_input.setText("TEST-001")
    page.name_input.setText("Test Connector")
    assert page.isComplete() is True
