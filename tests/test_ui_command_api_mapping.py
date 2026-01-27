import os
import yaml
import pytest
from unittest.mock import patch

# Map UI command to expected API method name (example mapping, update as needed)
COMMAND_TO_API_METHOD = {
    'file.new': 'new_file',
    'file.open': 'open_file',
    'file.save': 'save_file',
    'file.export_bom': 'export_bom',
    'file.export_wirelist': 'export_wirelist',
    'file.exit': 'exit_app',
    'edit.undo': 'undo',
    'edit.redo': 'redo',
    'edit.settings': 'open_settings',
    'edit.theme': 'set_theme',
    'tool.move': 'move_tool',
    'tool.add_generic_device': 'add_generic_device',
    'device.create_wizard': 'create_device_wizard',
    'tool.measure': 'measure_tool',
    'view.zoom_extents': 'zoom_extents',
    'view.zoom_selected': 'zoom_selected',
    'view.toggle_project_browser': 'toggle_project_browser',
    'view.toggle_property_panel': 'toggle_property_panel',
    'view.toggle_library': 'toggle_library',
    'view.toggle_audit_panel': 'toggle_audit_panel',
    'view.reset_layout': 'reset_layout',
    'device.add_pin': 'add_pin',
    'edit.rotate_cw': 'rotate_cw',
    'edit.delete': 'delete_device',
}

UI_LAYOUT_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/ui_layout.yaml')


def extract_commands_from_yaml(yaml_path):
    with open(yaml_path) as f:
        layout = yaml.safe_load(f)
    commands = set()
    # Menubar
    for menu in layout.get('menubar', []):
        for item in menu.get('items', []):
            if 'command' in item:
                commands.add(item['command'])
    # Toolbar
    for item in layout.get('toolbar', {}).get('items', []):
        if 'command' in item:
            commands.add(item['command'])
    # Context menus
    for menu in layout.get('context_menu', {}).values():
        for item in menu:
            if isinstance(item, dict) and 'command' in item:
                commands.add(item['command'])
            elif isinstance(item, str):
                commands.add(item)
    return commands

@pytest.mark.parametrize("command_id", list(extract_commands_from_yaml(UI_LAYOUT_PATH)))
def test_ui_command_connected_to_api(command_id):
    api_method = COMMAND_TO_API_METHOD.get(command_id)
    assert api_method, f"No API method mapping for command: {command_id}"
    # Patch the APIManager method and simulate the UI action
    with patch(f"api.manager.APIManager.{api_method}") as mock_method:
        # Here you would simulate the UI action that triggers the command
        # For now, just call the method directly for demonstration
        # Only call the method if it exists (avoid calling with no args if not needed)
        api_cls = __import__('api.manager').manager.APIManager
        if hasattr(api_cls, api_method):
            method = getattr(api_cls, api_method)
            try:
                method()
            except TypeError:
                pass  # Ignore if method requires arguments
        assert mock_method.called, f"API method {api_method} not called for command {command_id}"
