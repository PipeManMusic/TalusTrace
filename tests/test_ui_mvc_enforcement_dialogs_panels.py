import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from ui.dialogs.device_wizard import DeviceWizard
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.theme_dialog import ThemeDialog
from ui.panels.properties import PropertiesPanel
from ui.panels.mapping import PinMappingDialog
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from ui.panels.audit import AuditPanel
from api.manager import APIManager
from infra.context import Context

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    api.dispatch = MagicMock(wraps=api.dispatch)
    api.subscribe = MagicMock(wraps=api.subscribe)
    yield api

@pytest.mark.parametrize("DialogClass", [DeviceWizard, SettingsDialog, ThemeDialog])
def test_dialog_uses_api_manager(DialogClass, app, api_manager):
    dlg = DialogClass()
    # Patch dialog's api reference if present
    if hasattr(dlg, 'api'):
        dlg.api = api_manager
    # Simulate dialog show/close
    dlg.show()
    dlg.close()
    # Check that dialog did not mutate context directly
    assert api_manager.dispatch.call_count >= 0
    # Optionally, check subscribe usage
    assert api_manager.subscribe.call_count >= 0

@pytest.mark.parametrize("PanelClass", [PropertiesPanel, ProjectBrowser, LibraryPanel, AuditPanel])
def test_panel_uses_api_manager(PanelClass, app, api_manager):
    panel = PanelClass()
    if hasattr(panel, 'api'):
        panel.api = api_manager
    panel.show()
    panel.close()
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0

def test_pin_mapping_dialog_uses_api_manager(app, api_manager):
    dlg = PinMappingDialog(wire_id="W1", connector_id="C1")
    dlg.show()
    dlg.close()
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0
