import pytest
from api.actions import ActionRegistry

def test_action_registry_ui_hooks():
    registry = ActionRegistry()
    @registry.register('file.open', label='Open File', shortcut='Ctrl+O', category='File')
    def open_file(ctx):
        return 'opened'
    @registry.register('file.save', label='Save File', shortcut='Ctrl+S', category='File')
    def save_file(ctx):
        return 'saved'
    # Metadata
    meta = registry.get_action_metadata('file.open')
    assert meta['label'] == 'Open File'
    assert meta['shortcut'] == 'Ctrl+O'
    # List with metadata
    actions = dict(registry.list_registered_actions(with_meta=True))
    assert 'file.save' in actions
    assert actions['file.save']['category'] == 'File'
    # List without metadata
    ids = registry.list_registered_actions()
    assert 'file.open' in ids
    assert 'file.save' in ids
