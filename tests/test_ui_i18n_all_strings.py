import pytest
import yaml
import os
from ui.layout_manager import LayoutManager
from ui.panels.properties import PropertiesPanel
from ui.panels.audit import AuditPanel
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from ui.dialogs.device_wizard import DeviceWizard
from ui.dialogs.settings_dialog import SettingsDialog
from ui.dialogs.theme_dialog import ThemeDialog
from ui.panels.mapping import PinMappingDialog
from PySide6.QtWidgets import QApplication, QMainWindow

LANG_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/langs/en.yaml')
UI_LAYOUT_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/ui_layout.yaml')

@pytest.fixture(scope='module')
def lang_yaml():
    with open(LANG_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope='module')
def ui_layout():
    with open(UI_LAYOUT_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.mark.parametrize('key', [
    # Window/dialog titles
    'Talus Trace', 'Device Wizard', 'System Settings', 'Theme Editor',
    # Panel headers
    'Properties', 'Audit', 'Component Library', 'Harness Components',
    # Form field labels
    'Device Name:', 'Grid Size:', 'Screen PPI:', 'ID', 'Label', 'No Selection', 'Unknown Item',
    # Button labels
    'Create', 'Save', 'Cancel', 'Ok',
])
def test_ui_string_in_i18n(lang_yaml, key):
    # Check if the string or its key is present in the i18n yaml
    found = any(key in v or key == k for k, v in lang_yaml.items())
    assert found, f'Missing i18n for: {key}'

@pytest.mark.parametrize('menu_key', [
    'file_new', 'file_open', 'file_save', 'file_export_bom', 'file_export_wirelist', 'file_exit',
    'edit_undo', 'edit_redo', 'edit_settings', 'edit_theme',
    'tool_add_generic_device', 'device_create_wizard', 'tool_measure',
    'view_zoom_extents', 'view_zoom_selected', 'view_toggle_project_browser',
    'view_toggle_property_panel', 'view_toggle_library', 'view_toggle_audit_panel', 'view_reset_layout',
])
def test_menu_label_in_i18n(lang_yaml, menu_key):
    assert menu_key in lang_yaml, f'Missing menu label i18n: {menu_key}'

@pytest.mark.parametrize('context_key', [
    'device.add_pin', 'edit.rotate_cw', 'edit.delete',
])
def test_context_menu_label_in_i18n(lang_yaml, context_key):
    assert context_key in lang_yaml, f'Missing context menu label i18n: {context_key}'

# Additional tests for dialog error/info messages, tooltips, etc. can be added here
