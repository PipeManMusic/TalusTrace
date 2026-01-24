import pytest
from pathlib import Path
from api.actions import ActionRegistry

def test_action_registry_persistent_log(tmp_path):
    log_path = tmp_path / "actions.log"
    registry = ActionRegistry(log_path=log_path)
    called = []
    @registry.register('test.action')
    def handler(ctx):
        called.append(ctx['val'])
    registry.execute('test.action', {'val': 42})
    registry.execute('test.action', {'val': 99})
    # Check in-memory log
    assert len(registry.get_action_log()) == 2
    # Check persistent log
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) == 2
    import json
    entries = [json.loads(line) for line in lines]
    assert entries[0]['event_type'] == 'action'
    assert entries[0]['payload']['action_id'] == 'test.action'
    assert entries[1]['payload']['context']['val'] == 99
    assert called == [42, 99]
