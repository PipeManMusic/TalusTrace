import pytest
import yaml
import os
from ui.context_menu_manager import ContextMenuManager
from ui.i18n import I18N

UUID_LAYOUT_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/ui_layout_with_uuids.yaml')
UUID_I18N_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/langs/en_with_uuids.yaml')

@pytest.fixture(scope='module')
def uuid_layout():
    with open(UUID_LAYOUT_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope='module')
def uuid_i18n():
    with open(UUID_I18N_PATH, 'r') as f:
        return yaml.safe_load(f)

def get_all_context_menu_uuids(layout):
    uuids = set()
    context_menus = layout.get('context_menu', {})
    for entries in context_menus.values():
        for entry in entries:
            if isinstance(entry, dict) and 'uuid' in entry:
                uuids.add(entry['uuid'])
    return uuids

@pytest.mark.parametrize('uuid', [
    uuid for uuid in get_all_context_menu_uuids(yaml.safe_load(open(UUID_LAYOUT_PATH)))
])
def test_context_menu_uuid_has_i18n_label(uuid, uuid_i18n):
    assert uuid in uuid_i18n, f"Missing i18n label for context menu UUID: {uuid}"
    label = uuid_i18n[uuid]
    assert isinstance(label, str) and label.strip(), f"i18n label for UUID {uuid} is empty or not a string"
