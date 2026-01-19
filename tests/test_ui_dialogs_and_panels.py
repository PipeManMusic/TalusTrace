import pytest
from PySide6.QtWidgets import QApplication
from ui.dialogs.device_wizard import DeviceWizard
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.theme_dialog import ThemeDialog
from ui.panels.properties import PropertiesPanel
from ui.panels.mapping import PinMappingDialog
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from ui.panels.audit import AuditPanel

@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.mark.parametrize("DialogClass", [DeviceWizard, SettingsDialog, ThemeDialog])
def test_dialog_contact(DialogClass, app):
    dlg = DialogClass()
    dlg.show()
    assert dlg.isVisible()
    # Simulate basic interaction
    dlg.close()
    assert not dlg.isVisible()

@pytest.mark.parametrize("PanelClass", [PropertiesPanel, ProjectBrowser, LibraryPanel, AuditPanel])
def test_panel_contact(PanelClass, app):
    panel = PanelClass()
    panel.show()
    assert panel.isVisible()
    panel.close()
    assert not panel.isVisible()

def test_pin_mapping_dialog_contact(app):
    dlg = PinMappingDialog(wire_id="W1", connector_id="C1")
    dlg.show()
    assert dlg.isVisible()
    # Simulate pin selection
    dlg.pin_selector.setCurrentIndex(1)
    assert dlg.get_selected_pin() == dlg.pin_selector.currentText()
    dlg.close()
    assert not dlg.isVisible()
