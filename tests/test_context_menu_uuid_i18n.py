import pytest
import yaml
import os
from ui.context_menu_manager import ContextMenuManager
from ui.i18n import I18N

# Use the actual existing config files
LAYOUT_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/ui_layout.yaml')
ACTIONS_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/actions.yaml')
I18N_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/langs/en.yaml')

@pytest.fixture(scope='module')
def layout_config():
    with open(LAYOUT_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope='module')
def actions_config():
    with open(ACTIONS_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope='module')
def i18n_config():
    with open(I18N_PATH, 'r') as f:
        return yaml.safe_load(f)

def get_all_action_uuids(actions_config):
    """Extract all UUIDs from actions.yaml"""
    uuids = set()
    if actions_config and 'commands' in actions_config:
        for cmd in actions_config['commands']:
            if isinstance(cmd, dict) and 'uuid' in cmd:
                uuids.add(cmd['uuid'])
    return uuids

def get_all_context_menu_command_ids(layout):
    """Extract all command IDs from context_menu entries"""
    commands = set()
    context_menus = layout.get('context_menu', {})
    for entries in context_menus.values():
        for entry in entries:
            if isinstance(entry, dict) and 'command' in entry:
                commands.add(entry['command'])
    return commands

@pytest.mark.parametrize('uuid', [
    '7a1e2b3c-4d5e-678f-9012-abcdefabcdef',  # device.add_pin
    '4a88e033-860e-4b9b-9140-338b49c40e61',  # edit.rotate_cw
    'e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b',  # edit.delete
    'f1831bfa-9f66-461c-8a1d-6c5440dc314b',  # tool.add_generic_device
])
def test_context_menu_uuid_has_i18n_label(uuid, i18n_config):
    """Test that each context menu UUID has a corresponding i18n label"""
    assert uuid in i18n_config, f"Missing i18n label for context menu UUID: {uuid}"
    label = i18n_config[uuid]
    assert isinstance(label, str) and label.strip(), f"i18n label for UUID {uuid} is empty or not a string"

def test_all_action_uuids_have_i18n(actions_config, i18n_config):
    """Test that all actions with UUIDs have i18n labels"""
    action_uuids = get_all_action_uuids(actions_config)
    for uuid in action_uuids:
        assert uuid in i18n_config, f"Action UUID {uuid} missing i18n label"
        assert i18n_config[uuid].strip(), f"i18n label for UUID {uuid} is empty"
