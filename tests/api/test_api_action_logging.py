import pytest
from api import actions

def test_action_logging_and_stack_inspection():
    registry = actions.ActionRegistry()
    called = []
    @registry.register('test.action')
    def handler(ctx):
        called.append(ctx)
    # Execute actions
    registry.execute('test.action', {'foo': 1})
    registry.execute('test.action', {'bar': 2})
    log = registry.get_action_log()
    assert len(log) == 2
    assert log[0]['action_id'] == 'test.action'
    assert log[0]['context'] == {'foo': 1}
    assert log[1]['context'] == {'bar': 2}
    # Clear log
    registry.clear_action_log()
    assert registry.get_action_log() == []
    # Stack inspection: called list
    assert called == [{'foo': 1}, {'bar': 2}]
